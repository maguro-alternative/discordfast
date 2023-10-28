from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

import uuid
from typing import Dict,List

from pkg.aio_req import (
    aio_get_request,
    aio_post_request
)
from pkg.crypt import decrypt_password

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
    from model_types.table_type import LineBotColunm
    from model_types.line_type.line_oauth import LineOAuthData
    from model_types.environ_conf import EnvConf
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB
    from app.model_types.table_type import LineBotColunm
    from app.model_types.line_type.line_oauth import LineOAuthData
    from app.model_types.environ_conf import EnvConf

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN
DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

LINE_REDIRECT_URI = EnvConf.LINE_CALLBACK_URL
LINE_OAUTH_BASE_URL = EnvConf.LINE_OAUTH_BASE_URL

ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class Auth(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/auth/discord')
        async def discord_auth(
            request : Request
        ):
            # セッションの初期化
            if request.session.get('discord_user') != None:
                request.session.pop("discord_user")
            if request.session.get('discord_connection') != None:
                request.session.pop("discord_connection")
            if request.session.get("discord_oauth_data") != None:
                request.session.pop("discord_oauth_data")

            state = str(uuid.uuid4())
            request.session["state"] = state
            request.session['discord_react'] = True

            url = f"{DISCORD_REDIRECT_URL}&state={state}"

            return RedirectResponse(url=url)

        @self.router.get('/auth/line')
        async def line_auth(
            request : Request
        ):
            request.session['line_react'] = True
            return RedirectResponse(url='/line-login')