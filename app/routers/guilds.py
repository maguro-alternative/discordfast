from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict

from base.aio_req import (
    aio_get_request,
    search_guild,
    discord_oauth_check
)
from model_types.discord_type.discord_user_session import DiscordOAuthData,MatchGuild
from model_types.discord_type.discord_type import DiscordUser

from model_types.session_type import FastAPISession

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class GuildsView(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guilds')
        async def guilds(request:Request):
            # OAuth2トークンが有効かどうか判断
            if request.session.get('discord_oauth_data'):
                oauth_session = DiscordOAuthData(**request.session.get('discord_oauth_data'))
                user_session = DiscordUser(**request.session.get('discord_user'))
                print(f"アクセスしたユーザー:{user_session.username}")
                # トークンの有効期限が切れていた場合、再ログインする
                if not await discord_oauth_check(access_token=oauth_session.access_token):
                    return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            else:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            # Botが所属しているサーバを取得
            bot_in_guild_get = await aio_get_request(
                url = DISCORD_BASE_URL + '/users/@me/guilds',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # ログインユーザが所属しているサーバを取得
            user_in_guild_get = await aio_get_request(
                url = DISCORD_BASE_URL + '/users/@me/guilds',
                headers = {
                    'Authorization': f'Bearer {oauth_session.access_token}'
                }
            )

            # ログインユーザとBotが同じ所属を見つける
            match_guild = await search_guild(
                bot_in_guild_get = bot_in_guild_get,
                user_in_guild_get = user_in_guild_get
            )

            return templates.TemplateResponse(
                "guilds.html",
                {
                    "request": request,
                    "match_guild":match_guild,
                    "title":f"{user_session.username}のサーバ一覧"
                }
            )

        @self.router.get('/guilds/view')
        async def guilds(
            request:Request
        ):
            """
            サーバー一覧を取得

            Args:
                request (DiscordGuildsRequest): 暗号化されたアクセストークンが格納

            Returns:
                _type_: サーバー一覧
            """
            session = FastAPISession(**request.session)
            # デバッグモード
            if DEBUG_MODE == False:
                access_token = session.discord_oauth_data.access_token
                # ログインユーザが所属しているサーバを取得
                user_in_guild_get:List[Dict] = await aio_get_request(
                    url=f'{DISCORD_BASE_URL}/users/@me/guilds',
                    headers={
                        'Authorization': f'Bearer {access_token}'
                    }
                )
            else:
                user_in_guild_get:List[Dict] = [
                    {
                        'id'                :bot_guild.id,
                        'name'              :bot_guild.name,
                        'icon'              :bot_guild._icon,
                        'permissions'       :bot_guild.premium_tier,
                        'features'          :bot_guild.features,
                        'permissions_new'   :bot_guild.premium_tier
                    }
                    for bot_guild in self.bot.guilds
                ]
            user_guild_id = [
                bot_guild.id
                for bot_guild in self.bot.guilds
            ]

            join_guilds = [
                user_guild
                for user_guild in user_in_guild_get
                if int(user_guild.get('id')) in user_guild_id
            ]
            #MatchGuild(**join_guilds[0])

            return JSONResponse(content=join_guilds)