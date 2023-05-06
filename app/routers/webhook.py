from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import aiofiles

import os
import io
import pickle
from typing import List,Dict,Any

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    check_permission,
    oauth_check
)

USER = os.getenv('PGUSER')
PASSWORD = os.getenv('PGPASSWORD')
DATABASE = os.getenv('PGDATABASE')
HOST = os.getenv('PGHOST')
db = PostgresDB(
    user=USER,
    password=PASSWORD,
    database=DATABASE,
    host=HOST
)

DISCORD_BASE_URL = "https://discord.com/api"
REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guild/{guild_id}/webhook')
async def webhook(
    request:Request,
    guild_id:int    
):
    # OAuth2トークンが有効かどうか判断
    try:
        if not await oauth_check(access_token=request.session["oauth_data"]["access_token"]):
            return RedirectResponse(url=REDIRECT_URL,status_code=302)
    except KeyError:
        return RedirectResponse(url=REDIRECT_URL,status_code=302)
    # Botが所属しているサーバを取得
    TABLE = f'webhook_{guild_id}'

    # Discordサーバー内での権限をチェック(この場合管理者かどうか)
    permission_bool = await check_permission(
        guild_id=guild_id,
        user_id=request.session["user"]["id"],
        access_token=request.session["oauth_data"]["access_token"],
        permission_16=0x00000008
    )

    user_permission:str = 'normal'

    # 管理者の場合adminを代入
    if permission_bool == True:
        user_permission = 'admin'

    # キャッシュ読み取り
    async with aiofiles.open(
        file=f'{TABLE}.pickle',
        mode='rb'
    ) as f:
        pickled_bytes = await f.read()
        with io.BytesIO() as f:
            f.write(pickled_bytes)
            f.seek(0)
            table_fetch:List[Dict[str,Any]] = pickle.load(f)

    # webhook一覧を取得
    all_webhook = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/webhooks',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバの情報を取得
    guild = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバのチャンネル一覧を取得
    all_channel = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # 取得上限を定める
    limit = os.environ.get('USER_LIMIT',default=100)

    # サーバのメンバー一覧を取得
    guild_members = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members?limit={limit}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    return templates.TemplateResponse(
        "webhook.html",
        {
            "request": request, 
            "guild": guild,
            "guild_members":guild_members,
            "guild_webhooks":all_webhook,
            "table_webhooks":table_fetch,
            "channels":all_channel,
            "guild_id": guild_id,
            "user_permission":user_permission,
            "title": request.session["user"]['username']
        }
    )
