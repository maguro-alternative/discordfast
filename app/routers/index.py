from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

import os
from typing import Dict

from pkg.aio_req import aio_get_request
from pkg.oauth_check import discord_oauth_check,line_oauth_check
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser

from model_types.session_type import FastAPISession

from discord.ext import commands
try:
    from core.start import DBot
    from model_types.environ_conf import EnvConf
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.model_types.environ_conf import EnvConf

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN
# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE
class Index(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get("/")
        async def index(request: Request):
            # Discordの認証情報が有効かどうか判断
            if request.session.get('discord_oauth_data'):
                oauth_session = DiscordOAuthData(**request.session.get('discord_oauth_data'))
                user_session = DiscordUser(**request.session.get('discord_user'))
                print(f"アクセスしたユーザー:{user_session.username}")
                # トークンの有効期限が切れていた場合、認証情報を削除
                if not await discord_oauth_check(access_token=oauth_session.access_token):
                    request.session.pop('discord_oauth_data')

            bot_data:Dict = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/users/@me',
                headers={
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            return templates.TemplateResponse(
                'index.html',
                {
                    'request': request,
                    'bot_data':bot_data,
                    'title':'トップページ'
                }
            )

        @self.router.get("/index-discord")
        async def index_discord(request: Request):
            session = FastAPISession(**request.session)
            # デバッグモード
            if DEBUG_MODE == False:
                if session.discord_oauth_data != None:
                    access_token = session.discord_oauth_data.access_token
                    if not await discord_oauth_check(access_token=access_token):
                        request.session.pop('discord_oauth_data')
                        request.session.pop('discord_user')
                        return JSONResponse(
                            status_code=401,
                            content={
                                'message':'認証情報が無効です'
                            }
                        )
                    else:
                        json_content = {
                            "id":str(session.discord_user.id),
                            "username":session.discord_user.username,
                            "avatar":session.discord_user.avatar
                        }
                        return JSONResponse(
                            status_code=200,
                            content=json_content
                        )
                else:
                    return JSONResponse(
                        status_code=401,
                        content={
                            'message':'認証情報が無効です'
                        }
                    )

        @self.router.get("/index-line")
        async def index_line(request: Request):
            session = FastAPISession(**request.session)
            # デバッグモード
            if DEBUG_MODE == False:
                if session.line_oauth_data != None:
                    access_token = session.line_oauth_data.access_token
                    if not await line_oauth_check(access_token=access_token):
                        request.session.pop('line_oauth_data')
                        request.session.pop('line_user')
                        return JSONResponse(
                            status_code=401,
                            content={
                                'message':'認証情報が無効です'
                            }
                        )
                    else:
                        guild_id = request.session.get('guild_id')
                        if guild_id == None:
                            guild_id = str()
                        else:
                            guild_id = str(guild_id)
                        json_content = {
                            "id":session.line_user.sub,
                            "username":session.line_user.name,
                            "avatar":session.line_user.picture,
                            "guildId":guild_id
                        }
                        return JSONResponse(
                            status_code=200,
                            content=json_content
                        )
                else:
                    return JSONResponse(
                        status_code=401,
                        content={
                            'message':'認証情報が無効です'
                        }
                    )