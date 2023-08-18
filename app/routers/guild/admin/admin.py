from fastapi import APIRouter,Header
from fastapi.responses import RedirectResponse,HTMLResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Optional,Union

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    pickle_read,
    get_profile,
    return_permission,
    oauth_check,
    decrypt_password
)
from typing import List,Dict,Any,Tuple
from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser
from model_types.discord_type.discord_request_type import DiscordBaseRequest

from model_types.table_type import GuildSetPermission

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import DB

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class AdminView(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guild/{guild_id}/admin')
        async def admin(
            request:Request,
            guild_id:int
        ):
            # OAuth2トークンが有効かどうか判断
            if request.session.get('discord_oauth_data'):
                oauth_session = DiscordOAuthData(**request.session.get('discord_oauth_data'))
                user_session = DiscordUser(**request.session.get('discord_user'))
                # トークンの有効期限が切れていた場合、再ログインする
                if not await oauth_check(access_token=oauth_session.access_token):
                    return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            else:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)

            TABLE_NAME = 'guild_set_permissions'

            # 取得上限を定める
            limit = os.environ.get('USER_LIMIT',default=100)

            # サーバの情報を取得
            guild = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # サーバのメンバー一覧を取得
            guild_members = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members?limit={limit}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # サーバの権限を取得
            guild_user_permission = await return_permission(
                guild_id=guild_id,
                user_id=user_session.id,
                access_token=oauth_session.access_token
            )

            # キャッシュ読み取り
            #guild_table_fetch:List[Dict[str,Any]] = await pickle_read(filename=TABLE_NAME)
            guild_table = [
                #g
                #for g in guild_table_fetch
                #if int(g.get('guild_id')) == guild_id
            ]

            if DB.conn == None:
                await DB.connect()

            guild_table:List[Dict[str,Any]] = await DB.select_rows(
                table_name=TABLE_NAME,
                columns=[],
                where_clause={
                    'guild_id':guild_id
                }
            )

            user_permission:str = 'normal'

            # 管理者の場合
            if (guild_user_permission.administrator):
                user_permission = 'admin'

            # 管理者ではない場合、該当するサーバーidがない場合、終了
            if user_permission != 'admin' or len(guild_table) == 0:
                return HTMLResponse("404")

            return templates.TemplateResponse(
                "guild/admin/admin.html",
                {
                    "request": request,
                    "guild": guild,
                    "guild_members":guild_members,
                    "guild_id": guild_id,
                    "guild_table":guild_table[0],
                    "title":request.session["discord_user"]['username']
                }
            )

        @self.router.get('/guild/{guild_id}/admin/view')
        async def admin(
            guild_id:int,
            token   :Optional[str]=Header(None)
        ) -> JSONResponse:
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token:str = await decrypt_password(decrypt_password=token.encode('utf-8'))
                # Discordのユーザ情報を取得
                discord_user = await get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})
            TABLE_NAME = 'guild_set_permissions'

            for guild in self.bot.guilds:
                if guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE == False:
                        # サーバの権限を取得
                        permission = await return_permission(
                            guild_id=guild.id,
                            user_id=discord_user.id,
                            access_token=access_token
                        )
                    else:
                        from model_types.discord_type.guild_permission import Permission
                        permission = Permission()
                        permission.administrator = True
                    guild_members = [
                        {
                            'userId'            :member.id,
                            'userName'          :member.name,
                            'userDisplayName'   :member.display_name
                        }
                        for member in guild.members
                    ]
                    guild_roles = [
                        {
                            'roleId'    :role.id,
                            'roleName'  :role.name
                        }
                        for role in guild.roles
                    ]
                    p:List[Dict] = await DB.select_rows(
                        table_name=TABLE_NAME,
                        columns=[],
                        where_clause={
                            'guild_id':guild.id
                        }
                    )

                    # 管理者ではない場合、該当するサーバーidがない場合、終了
                    if permission.administrator == False or len(p) == 0:
                        return JSONResponse(content={'message':'404'})
                    guild_permission = GuildSetPermission(**p[0])

                    json_content = {
                        'guildMembers'              :guild_members,
                        'guildRoles'                :guild_roles,
                        'linePermission'            :guild_permission.line_permission,
                        'lineUserIdPermission'      :guild_permission.line_user_id_permission,
                        'lineRoleIdPermission'      :guild_permission.line_role_id_permission,
                        'lineBotPermission'         :guild_permission.line_bot_permission,
                        'lineBotUserIdPermission'   :guild_permission.line_bot_user_id_permission,
                        'lineBotRoleIdPermission'   :guild_permission.line_bot_role_id_permission,
                        'vcPermission'              :guild_permission.vc_permission,
                        'vcUserIdPermission'        :guild_permission.vc_user_id_permission,
                        'vcRoleIdPermission'        :guild_permission.vc_role_id_permission,
                        'webhookPermission'         :guild_permission.webhook_permission,
                        'webhookUserIdPermission'   :guild_permission.webhook_user_id_permission,
                        'webhookRoleIdPermission'   :guild_permission.webhook_role_id_permission
                    }

                    return JSONResponse(content=json_content)