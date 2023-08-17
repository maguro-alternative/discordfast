from fastapi import APIRouter,Header
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import Optional

from base.aio_req import (
    aio_get_request,
    oauth_check,
    return_permission,
    get_profile,
    pickle_read,
    decrypt_password
)
from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser
from model_types.discord_type.discord_request_type import DiscordBaseRequest

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class GuildSetView(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guild/{guild_id}')
        async def guild(
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

            # サーバの情報を取得
            guild = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # サーバの権限を取得
            permission = await return_permission(
                guild_id=guild_id,
                user_id=user_session.id,
                access_token=oauth_session.access_token
            )

            try:
                tasks = await pickle_read(
                    filename=f"task_{guild_id}"
                )
            except FileNotFoundError:
                tasks = list()

            return templates.TemplateResponse(
                "guild/guild.html",
                {
                    "request": request,
                    "guild": guild,
                    "guild_id": guild_id,
                    "tasks":tasks,
                    "permission":vars(permission),
                    "title":guild['name'] + "の設定項目一覧"
                }
            )

        @self.router.get('/guild/{guild_id}/view')
        async def guild(
            guild_id:int,
            token   :Optional[str]=Header(None)
        ) -> JSONResponse:
            """
            指定されたサーバidのページデータを取得

            Args:
                request (DiscordGuildRequest): _description_

            Returns:
                JSONResponse: _description_
            """
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token:str = await decrypt_password(decrypt_password=token.encode('utf-8'))
                # Discordのユーザ情報を取得
                discord_user = await get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

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

                        permission_code = await permission.get_permission_code()
                    else:
                        permission_code = 0
                    if guild.icon == None:
                        guild_icon_url = ''
                    else:
                        guild_icon_url = guild.icon.url
                    """
                    if db.conn == None:
                        await db.connect()

                    task_info = await db.select_rows(
                        table_name=f"task_{guild.id}",
                        columns=[],
                        where_clause={}
                    )
                    task_list# = LineBotColunm(**line_bot_info[0])
                    """

                    json_content = {
                        'guildIconUrl'  :guild_icon_url,
                        'guildName'     :guild.name,
                        'permissionCode':permission_code,
                        # 'taskList':task_list
                    }
                    return JSONResponse(content=json_content)

            return JSONResponse(content={'message':'not guild'})