from base.aio_req import (
    aio_get_request,
    return_permission,
    oauth_check
)
from starlette.requests import Request

from dotenv import load_dotenv
load_dotenv()

import os
from typing import Dict,List

from routers.session_base.user_session import OAuthData,User,MatchGuild

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_BASE_URL = "https://discord.com/api"

async def user_checker(
    request:Request,
    oauth_session:OAuthData,
    user_session:User
) -> int:
    """
    postリクエストが正しいものか判別する。

    param:

    """
    form = await request.form()
    # OAuth2トークンが有効かどうか判断
    try:
        await return_permission(
            guild_id=form["guild_id"],
            user_id=user_session.id,
            access_token=oauth_session.access_token
        )

        # トークンの有効期限が切れている場合、ログイン画面に遷移
        if (not await oauth_check(
                access_token=oauth_session.access_token
            )):
            return 302
        
        # サーバのメンバー一覧を取得
        guild_member = await aio_get_request(
            url = DISCORD_BASE_URL + f'/guilds/{form.get("guild_id")}/members/{user_session.id}',
            headers = {
                'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
            }
        )
        
        # ログインユーザがサーバーに所属していない場合(あり得ないリクエスト)
        if guild_member.get('message') != None:
            return 400

    except KeyError:
        return 400
    
    return 200