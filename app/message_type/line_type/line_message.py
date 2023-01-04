import json
import requests
from requests import Response

import datetime
import calendar
import os
import math
import asyncio
import time
import aiofiles

import aiohttp
from aiohttp import web
import subprocess
from typing import List

from dotenv import load_dotenv
load_dotenv()

from functools import partial

try:
    from message_type.line_type.class_type import Profile,GyazoJson
except:
    from app.message_type.line_type.class_type import Profile,GyazoJson

NOTIFY_URL = 'https://notify-api.line.me/api/notify'
NOTIFY_STATUS_URL = 'https://notify-api.line.me/api/status'
LINE_BOT_URL = 'https://api.line.me/v2/bot'
LINE_CONTENT_URL = 'https://api-data.line.me/v2/bot'

# LINEのgetリクエストを行う
async def line_get_request(url: str, token: str) -> json:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url = url,
            headers = {'Authorization': 'Bearer ' + token}
        ) as resp:
            return await resp.json()

# LINEのpostリクエストを行う
async def line_post_request(url: str, headers: dict, data: dict) -> json:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url = url,
            headers = headers,
            data = data
        ) as resp:
            return await resp.json()

class LineBotAPI:
    def __init__(self, notify_token: str, line_bot_token: str, line_group_id: str) -> None:
        self.notify_token = notify_token
        self.line_bot_token = line_bot_token
        self.line_group_id = line_group_id
        self.loop = asyncio.get_event_loop()

    # LINE Notifyでテキストメッセージを送信
    async def push_message_notify(self, message: str):
        data = {'message': f'message: {message}'}
        return await line_post_request(
            url = NOTIFY_URL, 
            headers = {'Authorization': f'Bearer {self.notify_token}'}, 
            data = data
        )
        #return requests.post(url=NOTIFY_URL, headers={'Authorization': f'Bearer {self.notify_token}'}, data=data)

    # LINE Notifyで画像を送信
    async def push_image_notify(self, message: str, image_url: str):
        if len(message) == 0:
            message = "画像を送信しました。"
        data = {
            'imageThumbnail': f'{image_url}',
            'imageFullsize': f'{image_url}',
            'message': f'{message}',
        }
        return await line_post_request(
            url = NOTIFY_URL, 
            headers = {'Authorization': f'Bearer {self.notify_token}'}, 
            data = data
        )
        #return requests.post(url=NOTIFY_URL, headers={'Authorization': f'Bearer {self.notify_token}'}, data=data)

    # 動画の送信(動画のみ)
    async def push_movie(self, preview_image: str, movie_urls: List[str]):
        data = []
        for movie_url in movie_urls:
            data.append({
                "type": "video",
                "originalContentUrl": movie_url,
                "previewImageUrl": preview_image
            })
        datas = {
            "to": self.line_group_id,
            "messages": data
        }
        return await line_post_request(
            url = LINE_BOT_URL + "/message/push",
            headers = {
                'Authorization': 'Bearer ' + self.line_bot_token,
                'Content-Type': 'application/json'
            },
            data = json.dumps(datas)
        )

    # 送ったメッセージ数を取得
    async def totalpush(self) -> int:
        r = await line_get_request(
            LINE_BOT_URL + "/message/quota/consumption",
            self.line_bot_token
        )
        return int(r["totalUsage"])

    # LINE Notifyのステータスを取得
    async def notify_status(self) -> Response:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = NOTIFY_STATUS_URL,
                headers = {'Authorization': 'Bearer ' + self.notify_token}
            ) as resp:
                return await resp

    # LINE Notifyの1時間当たりの上限を取得
    async def rate_limit(self) -> int:
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-Limit')
        return int(ratelimit)

    # LINE Notifyの1時間当たりの残りの回数を取得
    async def rate_remaining(self) -> int:
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-Remaining')
        return int(ratelimit)

    # LINE Notifyの1時間当たりの画像送信上限を取得
    async def rate_image_limit(self) -> int:
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-ImageLimit')
        return int(ratelimit)

    # LINE Notifyの1時間当たりの残り画像送信上限を取得
    async def rate_image_remaining(self) -> int:
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-ImageRemaining')
        return int(ratelimit)

    # 友達数、グループ人数をカウント
    async def friend(self):
        # グループIDが有効かどうか判断
        try:
            r = await line_get_request(
                LINE_BOT_URL + "/group/" + self.line_group_id + "/members/count",
                self.line_bot_token,
            )
            return r["count"]
        # グループIDなしの場合、友達数をカウント
        except KeyError:
            # 日付が変わった直後の場合、前日を参照
            if datetime.datetime.now().strftime('%H') == '00':
                before_day = datetime.date.today() + datetime.timedelta(days=-1)
                url = LINE_BOT_URL + "/insight/followers?date=" + before_day.strftime('%Y%m%d')
            else:
                url = LINE_BOT_URL + "/insight/followers?date=" + datetime.date.today().strftime('%Y%m%d')
            r = await line_get_request(
                url,
                self.line_bot_token,
            )
            return r["followers"] 

    # 当月に送信できるメッセージ数の上限目安を取得(基本1000,23年6月以降は200)
    async def pushlimit(self):
        r = await line_get_request(
            LINE_BOT_URL + "/message/quota",
            self.line_bot_token
        )
        return r["value"]


    # LINEのユーザプロフィールから名前を取得
    async def get_proflie(self, user_id: str):# -> Profile:
        # グループIDが有効かどうか判断
        try:
            r = await line_get_request(
                LINE_BOT_URL + f"/group/{self.line_group_id}/member/{user_id}",
                self.line_bot_token,
            )
        # グループIDが無効の場合、友達から判断
        except KeyError:
            r = await line_get_request(
                LINE_BOT_URL + f"/profile/{user_id}",
                self.line_bot_token,
            )
        return await Profile.new_from_json_dict(data=r)

    # LINEから画像データを取得し、Gyazoにアップロード
    async def get_image_byte(self, message_id: int):
        # 画像のバイナリデータを取得
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url = LINE_CONTENT_URL + f'/message/{message_id}/content',
                    headers={
                        'Authorization': 'Bearer ' + self.line_bot_token
                    }
            ) as bytes:
                image_bytes = bytes.content

                # Gyazoにアップロードする
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url = 'https://upload.gyazo.com/api/upload',
                        headers={
                            'Authorization': 'Bearer ' + os.environ['GYAZO_TOKEN'],
                            'imagedata': image_bytes
                        },
                        #files={
                            #'imagedata': image_bytes
                        #}
                    ) as gyazo_image:
                        return await GyazoJson.new_from_json_dict(gyazo_image.json())
        # 受け取ったjsonから画像のURLを生成
        # return f"https://i.gyazo.com/{gyazo_image['image_id']}.{gyazo_image['type']}"

    # LINEから受け取った動画を保存し、YouTubeに限定公開でアップロード
    async def movie_upload(self, message_id: int, display_name: str):
        # 動画のバイナリデータを取得
        #r=requests.get(url = LINE_CONTENT_URL + f'/message/{message_id}/content',headers={'Authorization': 'Bearer ' + self.line_bot_token})
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url = LINE_CONTENT_URL + f'/message/{message_id}/content',
                    headers={
                        'Authorization': 'Bearer ' + self.line_bot_token
                    }
            ) as bytes:
                #movies_bytes = bytes.content.iter_chunks()

                # mp4で保存
                async with aiofiles.open(".\movies\a.mp4", 'wb') as fd:
                #with open("./movies/a.mp4", 'wb') as fd:
                    async for chunk in bytes.content.iter_chunked(1024):
                    #for chunk in movies_bytes:
                        fd.write(chunk)

                # subprocessでupload_video.pyを実行、動画がYouTubeに限定公開でアップロードされる
                youtube_id = subprocess.run(
                    ['python', 'upload_video.py', f'--title="{display_name}の動画"', '--description="LINEからの動画"'],
                    capture_output=True
                )

                # 出力されたidを当てはめ、YouTubeの限定公開リンクを作成
                return f"https://youtu.be/{youtube_id.stdout.decode()}"



if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    #line = Notify(notify_token, line_bot_api, line_group_id)

    #start = time.time()
    token = os.environ['6_NOTIFY_TOKEN']
    resp = requests.get('https://notify-api.line.me/api/status', headers={'Authorization': f'Bearer {token}'})
    ratelimit = resp.headers.get("X-RateLimit-Limit")
    print(ratelimit)