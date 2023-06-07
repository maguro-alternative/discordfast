from fastapi import APIRouter,Request,Header
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

from base.aio_req import (
    aio_get_request
)

import os
import secrets

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BASE_URL = "https://discord.com/api"

@router.get("/discord-login")
async def discord_login(request: Request):
    # ランダムなstate値の生成
    state = secrets.token_urlsafe(16)
    request.session['state'] = state
    try:
        oauth_data:dict = await aio_get_request(
            url = DISCORD_BASE_URL + '/users/@me', 
            headers = { 
                'Authorization': f'Bearer {request.session["discord_oauth_data"]["access_token"]}' 
            }
        )
        if oauth_data.get('message') == '401: Unauthorized':
            return RedirectResponse(url=f"{REDIRECT_URL}&state={state}",status_code=302)
    except:
        return RedirectResponse(url=f"{REDIRECT_URL}&state={state}",status_code=302)
    return templates.TemplateResponse(
        'register.html',
        {
            'request': request,
        }
    )
 

@router.post("/register")
async def register_post(request: Request):
    # ホームページにリダイレクトする
    return RedirectResponse(url=REDIRECT_URL,status_code=302)