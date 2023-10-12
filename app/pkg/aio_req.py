import aiohttp
from typing import Dict,Union,List

# getリクエストを行う
async def aio_get_request(url: str, headers: dict) -> Union[Dict,List[Dict]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url = url,
            headers = headers
        ) as resp:
            return await resp.json()

# postリクエストを行う
async def aio_post_request(url: str, headers: dict, data: dict) -> Union[Dict,List[Dict]]:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url = url,
            headers = headers,
            data = data
        ) as resp:
            return await resp.json()
