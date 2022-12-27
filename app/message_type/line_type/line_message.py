import json
import requests
import datetime
import calendar
import os
import math
import asyncio
import time
import aiofiles

import subprocess
from typing import List

from dotenv import load_dotenv
load_dotenv()
try:
    from message_type.line_type.class_type import Profile,GyazoJson
except:
    from app.message_type.line_type.class_type import Profile,GyazoJson

NOTIFY_URL = 'https://notify-api.line.me/api/notify'
LINE_BOT_URL = 'https://api.line.me/v2/bot'

async def line_req(url: str, token: str) -> json:
    r = requests.get(url=url,headers={'Authorization': 'Bearer ' + token})
    return r.json()

class LineBotAPI:
    def __init__(self, notify_token: str, line_bot_token: str, line_group_id: str) -> None:
        self.notify_token = notify_token
        self.line_bot_token = line_bot_token
        self.line_group_id = line_group_id

    # LINE Notifyでテキストメッセージを送信
    async def push_message_notify(self, message: str):
        data = {'message': f'message: {message}'}
        return requests.post(url=NOTIFY_URL, headers={'Authorization': f'Bearer {self.notify_token}'}, data=data)

    # LINE Notifyで画像を送信
    async def push_image_notify(self, message: str, image_url: str):
        if len(message) == 0:
            message = "画像を送信しました。"
        data = {
            'imageThumbnail': f'{image_url}',
            'imageFullsize': f'{image_url}',
            'message': f'{message}',
        }
        # print(self.header)
        return requests.post(url=NOTIFY_URL, headers={'Authorization': f'Bearer {self.notify_token}'}, data=data)

    # 動画の送信(動画のみ)
    async def push_movie(self, preview_image: str, movie_urls: List[str]):
        data = []
        #if len(preview_image) == 0:
            #preview_image = ""
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
        return requests.post(
            url = LINE_BOT_URL + "/message/push",
            headers = {
                'Authorization': 'Bearer ' + self.line_bot_token,
                'Content-Type': 'application/json'
            },
            data=json.dumps(datas)
        )

    async def totalpush(self) -> int:
        return await line_req(
            LINE_BOT_URL + "/message/quota/consumption",
            self.line_bot_token
        )["totalUsage"]

    # 友達数、グループ人数をカウント
    async def friend(self):
        # グループIDが有効かどうか判断
        try:
            r = await line_req(
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
            r = await line_req(
                url,
                self.line_bot_token,
            )
            return r["followers"] 

    # 当月に送信できるメッセージ数の上限目安を取得(基本1000,23年6月以降は200)
    async def pushlimit(self):
        r = await line_req(
            LINE_BOT_URL + "/message/quota",
            self.line_bot_token
        )
        return r["value"]


    # LINEのユーザプロフィールから名前を取得
    async def get_proflie(self, user_id: str):# -> Profile:
        # グループIDが有効かどうか判断
        try:
            r = await line_req(
                LINE_BOT_URL + f"/group/{self.line_group_id}/member/{user_id}",
                self.line_bot_token,
            )
        # グループIDが無効の場合、友達から判断
        except KeyError:
            r = await line_req(
                LINE_BOT_URL + f"/profile/{user_id}",
                self.line_bot_token,
            )
        return await Profile.new_from_json_dict(data=r)

    # LINEから画像データを取得し、Gyazoにアップロード
    async def get_image_byte(self, message_id: int):
        # 画像のバイナリデータを取得
        image_bytes = requests.get(
            LINE_BOT_URL + f'/message/{message_id}/content',
            headers={
                'Authorization': 'Bearer ' + self.line_bot_token
            }
        ).content
        async with aiofiles.open(".\a.png",mode='wb') as f:
            await f.write(image_bytes)

        async with aiofiles.open(".\a.png", "rb") as f: 
            # Gyazoにアップロードする
            gyazo_image = requests.post(
                "https://upload.gyazo.com/api/upload",
                headers={
                    'Authorization': 'Bearer ' + os.environ['GYAZO_TOKEN'],
                    'imagedata': await f.read()
                },
                #files={
                    #'imagedata': image_bytes
                #}
            )#.json()
        print(gyazo_image.text)
        print(gyazo_image.headers)

        return await GyazoJson.new_from_json_dict(gyazo_image.json())
        # 受け取ったjsonから画像のURLを生成
        # return f"https://i.gyazo.com/{gyazo_image['image_id']}.{gyazo_image['type']}"

    # LINEから受け取った動画を保存し、YouTubeに限定公開でアップロード
    async def movie_upload(self, message_id: int, display_name: str):
        # 動画のバイナリデータを取得
        movies_bytes = requests.get(
            LINE_BOT_URL + f'/message/{message_id}/content',
            headers={
                'Authorization': 'Bearer ' + self.line_bot_token
            }
        ).iter_content()

        # mp4で保存
        with open(".\movies\a.mp4", 'wb') as fd:
        #with open("./movies/a.mp4", 'wb') as fd:
            for chunk in movies_bytes:
                fd.write(chunk)

        # subprocessでupload_video.pyを実行、動画がYouTubeに限定公開でアップロードされる
        youtube_id = subprocess.run(
            ['python', 'upload_video.py', f'--title="{display_name}の動画"', '--description="LINEからの動画"'],
            capture_output=True)

        # 出力されたidを当てはめ、YouTubeの限定公開リンクを作成
        return f"https://youtu.be/{youtube_id.stdout.decode()}"



if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    #line = Notify(notify_token, line_bot_api, line_group_id)

    start = time.time()