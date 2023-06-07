from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.aio_req import (
    aio_get_request,
    aio_post_request
)

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/callback/')
async def callback(
    code:str,
    state: str,
    request:Request
):
    # 旧セッションの初期化
    if request.session.get('user') != None:
        request.session.pop("user")
    if request.session.get('connection') != None:
        request.session.pop("connection")
    if request.session.get("oauth_data") != None:
        request.session.pop("oauth_data")
    
    # セッションの初期化
    if request.session.get('discord_user') != None:
        request.session.pop("discord_user")
    if request.session.get('discord_connection') != None:
        request.session.pop("discord_connection")
    if request.session.get("discord_oauth_data") != None:
        request.session.pop("discord_oauth_data")

    # stateが一緒しない場合、400で終了
    if request.session.get("state") != state:
        raise HTTPException(status_code=400, detail="認証失敗")
    # stateが一致した場合、削除して続行
    else:
        request.session.pop("state")
        
    authorization_code = code

    request_postdata = {
        'client_id': os.environ.get('DISCORD_CLIENT_ID'), 
        'client_secret': os.environ.get('DISCORD_CLIENT_SECRET'), 
        'grant_type': 'authorization_code', 
        'code': authorization_code, 
        'redirect_uri': os.environ.get('DISCORD_CALLBACK_URL')
    }

    responce_json = await aio_post_request(
        url = DISCORD_BASE_URL + '/oauth2/token',
        data = request_postdata,
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )

    request.session["discord_oauth_data"] = responce_json

    request.session["discord_user"] = await aio_get_request(
        url = DISCORD_BASE_URL + '/users/@me', 
        headers = { 
            'Authorization': f'Bearer {responce_json["access_token"]}' 
        }
    )

    request.session["discord_connection"] = await aio_get_request(
        url = DISCORD_BASE_URL + '/users/@me/connections', 
        headers = { 
            'Authorization': f'Bearer {responce_json["access_token"]}' 
        }
    )

    # ホームページにリダイレクトする
    return RedirectResponse(url="/guilds")