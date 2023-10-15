from fastapi import APIRouter
from fastapi.responses import RedirectResponse,HTMLResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from pkg.aio_req import aio_get_request
from pkg.oauth_check import discord_oauth_check,discord_get_profile
from pkg.permission import return_permission
from typing import List,Dict,Any
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser

from model_types.session_type import FastAPISession

from model_types.table_type import GuildSetPermission

from model_types.environ_conf import EnvConf

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

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
                if not await discord_oauth_check(access_token=oauth_session.access_token):
                    return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            else:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)

            TABLE_NAME = 'guild_set_permissions'

            # 取得上限を定める
            limit = EnvConf.USER_LIMIT

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
                user_id=user_session.id,
                guild=[
                    guild
                    for guild in self.bot.guilds
                    if guild.id == guild_id
                ][0]
            )

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
            request:Request
        ) -> JSONResponse:
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token = session.discord_oauth_data.access_token
                # Discordのユーザ情報を取得
                discord_user = await discord_get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})
            TABLE_NAME = 'guild_set_permissions'

            for guild in self.bot.guilds:
                if guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE:
                        from model_types.discord_type.guild_permission import Permission
                        permission = Permission()
                        permission.administrator = True
                    else:
                        # サーバの権限を取得
                        permission = await return_permission(
                            user_id=discord_user.id,
                            guild=guild
                        )
                    guild_members = [
                        {
                            'userId'            :str(member.id),
                            'userName'          :member.name,
                            'userDisplayName'   :member.display_name
                        }
                        for member in guild.members
                    ]
                    guild_roles = [
                        {
                            'roleId'    :str(role.id),
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
                        'guildIcon'                 :guild._icon,
                        'guildName'                 :guild.name,
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