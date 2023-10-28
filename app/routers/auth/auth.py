from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request

import uuid

from discord.ext import commands
try:
    from core.start import DBot
    from model_types.environ_conf import EnvConf
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.model_types.environ_conf import EnvConf

DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

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