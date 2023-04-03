from fastapi import APIRouter,Request,Header
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from base.aio_req import (
    aio_get_request
)

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

router = APIRouter()

DISCORD_BASE_URL = "https://discord.com/api"

@router.get("/")
async def index(request: Request):
    try:
        oauth_data:dict = await aio_get_request(
            url = DISCORD_BASE_URL + '/users/@me', 
            headers = { 
                'Authorization': f'Bearer {request.session["oauth_data"]["access_token"]}' 
            }
        )
        if oauth_data.get('message') == '401: Unauthorized':
            request.session.pop("oauth_data")
    except KeyError:
        if request.session.get("oauth_data") != None:
            request.session.pop("oauth_data")
    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'title':'トップページ'
        }
    )


# sessionの中身(dict)
"""

{
    'oauth_data': {
        'access_token': str, 
        'expires_in': int, 
        'refresh_token': str, 
        'scope': str, 
        'token_type': str
    }, 
    'user': {
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
    'connection': [
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