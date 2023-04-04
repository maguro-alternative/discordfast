import json
import aiohttp
from typing import List

import os


DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# getリクエストを行う
async def aio_get_request(url: str, headers: dict) -> json:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url = url,
            headers = headers
        ) as resp:
            return await resp.json()

# postリクエストを行う
async def aio_post_request(url: str, headers: dict, data: dict) -> json:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url = url,
            headers = headers,
            data = data
        ) as resp:
            return await resp.json()

async def search_guild(
    bot_in_guild_get:List[dict],
    user_in_guild_get:List[dict]
):

    bot_guild_id = []
    user_guild_id = []
    match_guild = []

    for bot_guild in bot_in_guild_get:
        bot_guild_id.append(bot_guild['id'])

    for user_guild in user_in_guild_get:
        user_guild_id.append(user_guild['id'])
            
    if len(bot_guild_id) < len(user_guild_id):
        for guild_id,guild in zip(bot_guild_id,bot_in_guild_get):
            if guild_id in user_guild_id:
                match_guild.append(guild)
    else:
        for guild_id,guild in zip(user_guild_id,user_in_guild_get):
            if guild_id in bot_guild_id:
                match_guild.append(guild)

    return match_guild


async def search_role(
    guild_role_get:List[dict],
    user_role_get:List[dict]
) -> List[dict]:
    """
    ユーザがサーバ内で持っているロールの詳細を取得する
    guild_role_get  :List[dict]
        サーバにある全てのロール
    user_role_get   :List[dict]
        ユーザ情報
    """
    guild_role_id = []
    user_role_id = []
    match_role = []

    for guild_role in guild_role_get:
        guild_role_id.append(guild_role['id'])

    for user_guild in user_role_get["roles"]:
        user_role_id.append(user_guild)
            
    for role_id,role in zip(guild_role_id,guild_role_get):
        if role_id in user_role_id:
            match_role.append(role)

    return match_role

async def check_permission(
    guild_id:int,
    user_id:int,
    access_token:str,
    permission_16:int
) -> bool:
    """
    指定されたユーザが権限を持っているか確認

    guild_id        :int
        サーバのid
    user_id         :int
        ユーザのid
    access_token    :str
        ユーザのアクセストークン
    permission_16   :int
        確認する権限、16進数で構成されている
        詳細はdiscordのリファレンスを参照
    """
    # 指定されたパーミッションはあるか
    user_permission:bool = False

    # ログインユーザの情報を取得
    guild_user = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{user_id}',
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
            'Authorization': f'Bearer {access_token}'
        }
    )

    permission = None

    # サーバでの権限を取得
    for info in guild_info:
        if str(guild_id) == info["id"]:
            permission = info["permissions"]
            break

    if len(match_role) == 0:
        if permission & permission_16 == permission_16:
            user_permission = True

    for role in match_role:
        # サーバー管理者であるかどうかを調べる
        if (permission & permission_16 == permission_16 or
            int(role["permissions"]) & permission_16 == permission_16):
            user_permission = True
            break

    return user_permission