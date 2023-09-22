from base.aio_req import (
    return_permission,
    discord_oauth_check
)
from starlette.requests import Request
from discord import Guild

from dotenv import load_dotenv
load_dotenv()

import os
from typing import Dict,List

from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_BASE_URL = "https://discord.com/api"

async def user_checker(
    oauth_session:DiscordOAuthData,
    user_session:DiscordUser,
    guild:Guild
) -> int:
    """
    postリクエストが正しいものか判別する。

    param:

    """
    # OAuth2トークンが有効かどうか判断

    await return_permission(
        user_id=user_session.id,
        guild=guild
    )

    # トークンの有効期限が切れている場合、ログイン画面に遷移
    if (not await discord_oauth_check(
            access_token=oauth_session.access_token
        )):
        return 302

    member_ids = [
        member.id
        for member in guild.members
    ]

    if user_session.id not in member_ids:
        return 400

    return 200