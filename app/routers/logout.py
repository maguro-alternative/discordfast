from fastapi import APIRouter,Request
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BASE_URL = "https://discord.com/api"

@router.get("/discord-logout")
async def discord_logout(request: Request):
    # セッションの初期化
    if request.session.get('discord_user') != None:
        request.session.pop("discord_user")
    if request.session.get('discord_connection') != None:
        request.session.pop("discord_connection")
    if request.session.get("discord_oauth_data") != None:
        request.session.pop("discord_oauth_data")

    # 旧セッションの初期化
    if request.session.get('user') != None:
        request.session.pop("user")
    if request.session.get('connection') != None:
        request.session.pop("connection")
    if request.session.get("oauth_data") != None:
        request.session.pop("oauth_data")

    # ホームページにリダイレクトする
    return RedirectResponse(url="/")