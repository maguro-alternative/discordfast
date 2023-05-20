from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict,Any

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    pickle_read,
    return_permission,
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

    # ログインユーザの情報を取得
    guild_user = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{request.session["user"]["id"]}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )
    role_list = [g for g in guild_user["roles"]]


    # サーバの権限を取得
    guild_user_permission = await return_permission(
        guild_id=guild_id,
        user_id=request.session["user"]["id"],
        access_token=request.session["oauth_data"]["access_token"]
    )

    # パーミッションの番号を取得
    permission_code = await guild_user_permission.get_permission_code()

    # キャッシュ読み取り
    guild_table_fetch:List[Dict[str,Any]] = await pickle_read(filename='guild_set_permissions')
    guild_table = [
        g 
        for g in guild_table_fetch 
        if int(g.get('guild_id')) == guild_id
    ]
    guild_permission_code = 8
    guild_permission_user = list()
    guild_permission_role = list()
    if len(guild_table) > 0:
        guild_permission_code = int(guild_table[0].get('webhook_permission'))
        guild_permission_user = [
            user 
            for user in guild_table[0].get('webhook_user_id_permission')
        ]
        guild_permission_role = [
            role
            for role in guild_table[0].get('webhook_role_id_permission')
        ]

    and_code = guild_permission_code & permission_code
    admin_code = 8 & permission_code

    user_permission:str = 'normal'

    # 許可されている場合、管理者の場合
    if (and_code == permission_code or 
        admin_code == 8 or
        request.session['user']['id'] in guild_permission_user or
        len(set(guild_permission_role) & set(role_list)) > 0
        ):
        user_permission = 'admin'

    # キャッシュ読み取り
    table_fetch:List[Dict[str,Any]] = await pickle_read(filename=TABLE)

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
