from fastapi import APIRouter
from fastapi.responses import RedirectResponse,HTMLResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from base.aio_req import (
    aio_get_request,
    pickle_read,
    return_permission,
    oauth_check
)
from typing import List,Dict,Any,Tuple
from routers.session_base.user_session import OAuthData,User

DISCORD_BASE_URL = "https://discord.com/api"
REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guild/{guild_id}/admin')
async def admin(
    request:Request,
    guild_id:int
):
    # OAuth2トークンが有効かどうか判断
    if request.session.get('oauth_data'):
        oauth_session = OAuthData(**request.session.get('oauth_data'))
        user_session = User(**request.session.get('user'))
        # トークンの有効期限が切れていた場合、再ログインする
        if not await oauth_check(access_token=oauth_session.access_token):
            return RedirectResponse(url=REDIRECT_URL,status_code=302)
    else:
        return RedirectResponse(url=REDIRECT_URL,status_code=302)
    
    TABLE_NAME = 'guild_set_permissions'

    # 取得上限を定める
    limit = os.environ.get('USER_LIMIT',default=100)

    # サーバの情報を取得
    guild = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバのメンバー一覧を取得
    guild_members = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members?limit={limit}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバの権限を取得
    guild_user_permission = await return_permission(
        guild_id=guild_id,
        user_id=user_session.id,
        access_token=oauth_session.access_token
    )

    # キャッシュ読み取り
    guild_table_fetch:List[Dict[str,Any]] = await pickle_read(filename=TABLE_NAME)
    guild_table = [
        g 
        for g in guild_table_fetch 
        if int(g.get('guild_id')) == guild_id
    ]
    
    user_permission:str = 'normal'

    # 管理者の場合
    if (guild_user_permission.administrator):
        user_permission = 'admin'

    # 管理者ではない場合、該当するサーバーidがない場合、終了
    if user_permission != 'admin' or len(guild_table) == 0:
        return HTMLResponse("404")
    
    return templates.TemplateResponse(
        "guild/admin/admin.html",
        {
            "request": request, 
            "guild": guild,
            "guild_members":guild_members,
            "guild_id": guild_id,
            "guild_table":guild_table[0],
            "title":request.session["user"]['username']
        }
    )