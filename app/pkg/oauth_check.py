from typing import Optional

from pkg.aio_req import aio_get_request
from model_types.discord_type.discord_type import DiscordUser
from model_types.environ_conf import EnvConf

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
LINE_BASE_URL = EnvConf.LINE_BASE_URL

async def discord_oauth_check(
    access_token:str
) -> bool:
    """
    OAuth2のトークンが有効か判断する

    param:
    access_token:str
        OAuth2のトークン

    return:
    bool
        トークンが有効な場合、True
        無効の場合、Falseが返される
    """
    oauth_data:dict = await aio_get_request(
        url=f'{DISCORD_BASE_URL}/users/@me',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )
    if oauth_data.get('message') == '401: Unauthorized':
        return False
    else:
        return True

async def line_oauth_check(
    access_token:str
) -> bool:
    """
    OAuth2のトークンが有効か判断する

    param:
    access_token:str
        OAuth2のトークン

    return:
    bool
        トークンが有効な場合、True
        無効の場合、Falseが返される
    """
    oauth_data:dict = await aio_get_request(
        url=f'{LINE_BASE_URL}/oauth2/v2.1/verify?access_token={access_token}',
        headers={}
    )
    if oauth_data.get('error_description') == 'access token expired':
        return False
    else:
        return True

async def discord_get_profile(
    access_token:str
) -> Optional[DiscordUser]:
    """
    OAuth2のトークンが有効か判断する

    param:
    access_token:str
        OAuth2のトークン

    return:
    bool
        トークンが有効な場合、True
        無効の場合、Falseが返される
    """
    oauth_data:dict = await aio_get_request(
        url=f'{DISCORD_BASE_URL}/users/@me',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )
    if oauth_data.get('message') == '401: Unauthorized':
        return None
    else:
        user = DiscordUser(**oauth_data)
        return user