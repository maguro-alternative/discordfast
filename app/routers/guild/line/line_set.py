from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates


from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict,Any
from itertools import groupby,chain
from cryptography.fernet import Fernet

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    pickle_read,
    return_permission,
    oauth_check,
    sort_discord_channel,
    decrypt_password
)
from routers.session_base.user_session import DiscordOAuthData,DiscordUser

from message_type.discord_type.message_creater import ReqestDiscord
from base.guild_permission import Permission

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]


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

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guild/{guild_id}/line-set')
async def line_set(
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

    # 使用するデータベースのテーブル名
    TABLE = f'line_bot'

    # サーバのチャンネル一覧を取得
    all_channel = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ソート後のチャンネル一覧
    all_channel_sort = await sort_discord_channel(all_channel=all_channel)

    # サーバの情報を取得
    guild = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ログインユーザの情報を取得
    guild_user = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{user_session.id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # アクティブスレッドを取得
    active_threads = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/threads/active',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # フォーラムチャンネルがあるか調べる
    threads_list = [
        t
        for t in all_channel_sort
        if int(t.get('type')) == 15
    ]

    for a_thead in active_threads.get('threads'):
        all_channel_sort.append(a_thead)

    archived_threads = list()

    for thread in threads_list:
        thread_id = thread.get('id')
        # アーカイブスレッドを取得
        archived_threads = await aio_get_request(
            url = DISCORD_BASE_URL + f'/channels/{thread_id}/threads/archived/public',
            headers = {
                'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
            }
        )
        for a_thead in archived_threads.get('threads'):
            all_channel_sort.append(a_thead)

    role_list = [
        g
        for g in guild_user["roles"]
    ]

    # サーバの権限を取得
    guild_user_permission = await return_permission(
        guild_id=guild_id,
        user_id=user_session.id,
        access_token=oauth_session.access_token
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
        guild_permission_code = int(guild_table[0].get('line_bot_permission'))
        guild_permission_user = [
            user
            for user in guild_table[0].get('line_bot_user_id_permission')
        ]
        guild_permission_role = [
            role
            for role in guild_table[0].get('line_bot_role_id_permission')
        ]

    and_code = guild_permission_code & permission_code
    admin_code = 8 & permission_code
    user_permission:str = 'normal'

    # 許可されている場合、管理者の場合
    if (and_code == permission_code or
        admin_code == 8 or
        user_session.id in guild_permission_user or
        len(set(guild_permission_role) & set(role_list)) > 0
        ):
        user_permission = 'admin'

    # キャッシュ読み取り
    table_fetch:List[Dict[str,Any]] = await pickle_read(filename=TABLE)

    line_row = {}

    # 各項目をフロント部分に渡す
    for table in table_fetch:
        if int(table.get('guild_id')) == guild_id:
            line_notify_token:str = await decrypt_password(encrypted_password=bytes(table.get('line_notify_token')))
            line_bot_token:str = await decrypt_password(encrypted_password=bytes(table.get('line_bot_token')))
            line_bot_secret:str = await decrypt_password(encrypted_password=bytes(table.get('line_bot_secret')))
            line_group_id:str = await decrypt_password(encrypted_password=bytes(table.get('line_group_id')))
            line_client_id:str = await decrypt_password(encrypted_password=bytes(table.get('line_client_id')))
            line_client_secret:str = await decrypt_password(encrypted_password=bytes(table.get('line_client_secret')))
            default_channel_id:int = int(table.get('default_channel_id'))
            debug_mode:bool = bool(table.get('debug_mode'))

            line_row = {
                'line_notify_token':line_notify_token,
                'line_bot_token':line_bot_token,
                'line_bot_secret':line_bot_secret,
                'line_group_id':line_group_id,
                'line_client_id':line_client_id,
                'line_client_secret':line_client_secret,
                'default_channel_id':default_channel_id,
                'debug_mode':debug_mode
            }


    return templates.TemplateResponse(
        "guild/line/lineset.html",
        {
            "request": request,
            "guild": guild,
            "guild_id": guild_id,
            "all_channel": all_channel_sort,
            "line_row":line_row,
            "user_permission":user_permission,
            "title": "LINEBOTおよびグループ設定/" + guild['name']
        }
    )