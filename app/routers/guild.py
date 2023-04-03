from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.aio_req import (
    aio_get_request,
    search_role
)

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guild/{guild_id}')
async def guild(
    request:Request,
    guild_id:int
):
    # ログインユーザの情報を取得
    guild_user = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{request.session["user"]["id"]}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバのロールを取得
    guild_role = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/roles',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ログインユーザのロールの詳細を取得
    match_role = await search_role(
        guild_role_get = guild_role,
        user_role_get = guild_user
    )

    # ログインユーザの所属しているサーバを取得
    guild_info = await aio_get_request(
        url = DISCORD_BASE_URL + f'/users/@me/guilds',
        headers = {
            'Authorization': f'Bearer {request.session["oauth_data"]["access_token"]}'
        }
    )

    # サーバの情報を取得
    guild = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバでの権限を取得
    for info in guild_info:
        if str(guild_id) == info["id"]:
            permission = info["permissions"]
            break

    user_permission = 'normal'

    if len(match_role) == 0:
        if permission & 0x00000008 == 0x00000008:
            user_permission = 'admin'
        elif permission & 0x00000001 == 0x00000001:
            user_permission = 'friend'

    for role in match_role:
        # サーバー管理者であるかどうかを調べる
        if (
            permission & 0x00000008 == 0x00000008 or
            int(role["permissions"]) & 0x00000008 == 0x00000008
        ):
            print("指定したユーザーはサーバー管理者です。")
            user_permission = 'admin'
            break
        if (
            permission & 0x00000001 == 0x00000001 or
            int(role["permissions"]) & 0x00000001 == 0x00000001
        ):
            print("指定したユーザーは招待リンクを発行できます。")
            user_permission = 'friend'
            break

    return templates.TemplateResponse(
        "guild.html",
        {
            "request": request, 
            "guild": guild,
            "guild_id": guild_id,
            "user_permission":user_permission,
            "title":request.session["user"]['username']
        }
    )