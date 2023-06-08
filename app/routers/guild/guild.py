from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.aio_req import (
    aio_get_request,
    oauth_check,
    return_permission
)
from routers.session_base.user_session import DiscordOAuthData,DiscordUser

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guild/{guild_id}')
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

    return templates.TemplateResponse(
        "guild/guild.html",
        {
            "request": request, 
            "guild": guild,
            "guild_id": guild_id,
            "permission":vars(permission),
            "title":guild['name'] + "の設定項目一覧"
        }
    )