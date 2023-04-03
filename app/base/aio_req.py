import json
import aiohttp
from typing import List

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
):

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
