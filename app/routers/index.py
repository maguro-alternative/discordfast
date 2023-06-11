from fastapi import APIRouter,Request,Header
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

import os

from base.aio_req import (
    aio_get_request,
    oauth_check
)
from routers.session_base.user_session import DiscordOAuthData,DiscordUser

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

router = APIRouter()

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

@router.get("/")
async def index(request: Request):
    # Discordの認証情報が有効かどうか判断
    if request.session.get('discord_oauth_data'):
        oauth_session = DiscordOAuthData(**request.session.get('discord_oauth_data'))
        user_session = DiscordUser(**request.session.get('discord_user'))
        print(f"アクセスしたユーザー:{user_session.username}")
        # トークンの有効期限が切れていた場合、認証情報を削除
        if not await oauth_check(access_token=oauth_session.access_token):
            request.session.pop('discord_oauth_data')
    
    bot_data:dict = await aio_get_request(
        url = DISCORD_BASE_URL + '/users/@me', 
        headers = { 
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}' 
        }
    )

    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'bot_data':bot_data,
            'title':'トップページ'
        }
    )


# sessionの中身(dict)
"""

{
    'discord_oauth_data': {
        'access_token': str, 
        'expires_in': int, 
        'refresh_token': str, 
        'scope': str, 
        'token_type': str
    }, 
    'discord_user': {
        'id': int, 
        'username': str, 
        'global_name': str, 
        'display_name': str, 
        'avatar': str(16進数), 
        'avatar_decoration': str, 
        'discriminator': int, 
        'public_flags': int, 
        'flags': int, 
        'banner': str(16進数), 
        'banner_color': str, 
        'accent_color': int, 
        'locale': str, 
        'mfa_enabled': bool, 
        'premium_type': int
    }, 
    'discord_connection': [
        {
            'type': 'epicgames', 
            'id': str, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'github', 
            'id': int, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'instagram', 
            'id': int, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'spotify', 
            'id': str, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'steam', 
            'id': int, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'twitch', 
            'id': int, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'twitter', 
            'id': int, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'xbox', 
            'id': int, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }, 
        {
            'type': 'youtube', 
            'id': str, 
            'name': str, 
            'visibility': int, 
            'friend_sync': bool, 
            'show_activity': bool, 
            'verified': bool, 
            'two_way_link': bool, 
            'metadata_visibility': int
        }
    ]
}

"""