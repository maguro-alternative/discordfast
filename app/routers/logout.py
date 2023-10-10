from fastapi import APIRouter,Request
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BASE_URL = "https://discord.com/api"


class Logout(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get("/discord-logout")
        async def discord_logout(request: Request):
            # セッションの初期化
            if request.session.get('discord_user') != None:
                request.session.pop("discord_user")
            if request.session.get('discord_connection') != None:
                request.session.pop("discord_connection")
            if request.session.get("discord_oauth_data") != None:
                request.session.pop("discord_oauth_data")

            if request.session.get('discord_react'):
                request.session.pop("discord_react")
                return RedirectResponse(url=f'{os.environ.get("REACT_URL")}')
            else:
                # ホームページにリダイレクトする
                return RedirectResponse(url="/")

        @self.router.get("/line-logout")
        async def line_logout(request: Request):
            # セッションの初期化
            if request.session.get('line_user') != None:
                request.session.pop("line_user")
            if request.session.get("line_oauth_data") != None:
                request.session.pop("line_oauth_data")
            if request.session.get('guild_id'):
                request.session.pop('guild_id')

            if request.session.get('line_react'):
                request.session.pop("line_react")
                return RedirectResponse(url=f'{os.environ.get("REACT_URL")}')
            else:
                # ホームページにリダイレクトする
                return RedirectResponse(url="/")