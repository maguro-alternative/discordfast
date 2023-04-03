from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.aio_req import (
    aio_get_request,
    search_guild
)

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guilds')
async def guilds(request:Request):
    # Botが所属しているサーバを取得
    bot_in_guild_get = await aio_get_request(
        url = DISCORD_BASE_URL + '/users/@me/guilds',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ログインユーザが所属しているサーバを取得
    user_in_guild_get = await aio_get_request(
        url = DISCORD_BASE_URL + '/users/@me/guilds',
        headers = {
            'Authorization': f'Bearer {request.session["oauth_data"]["access_token"]}'
        }
    )

    # ログインユーザとBotが同じ所属を見つける
    match_guild = await search_guild(
        bot_in_guild_get = bot_in_guild_get,
        user_in_guild_get = user_in_guild_get
    )

    return templates.TemplateResponse(
        "guilds.html",
        {
            "request": request, 
            "match_guild":match_guild,
            "title":request.session["user"]['username']+"のサーバ一覧"
        }
    )