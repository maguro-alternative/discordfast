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

@router.get("/logout")
async def register_get(request: Request):
    # セッションの初期化
    if request.session:
        request.session.pop("user")
        request.session.pop("connection")
    if request.session.get("oauth_data") != None:
        request.session.pop("oauth_data")

    # ホームページにリダイレクトする
    return RedirectResponse(url="/")