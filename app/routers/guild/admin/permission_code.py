from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from pkg.oauth_check import discord_oauth_check

from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser
from model_types.environ_conf import EnvConf

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class PermissionCode(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guild/{guild_id}/admin/permission-code')
        async def per_code(
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

            return templates.TemplateResponse(
                "permission.html"
            )