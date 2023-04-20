import json
import requests
from requests import Response

import datetime

import os
import io
import asyncio
from functools import partial

import aiohttp
import subprocess
from typing import List,Dict

from dotenv import load_dotenv
load_dotenv()

try:
    from message_type.line_type.line_type import Profile,GyazoJson
    from message_type.youtube_upload import YouTubeUpload
    from message_type.file_type import Audio_Files
except:
    from app.message_type.line_type.line_type import Profile,GyazoJson
    from app.message_type.youtube_upload import YouTubeUpload
    from app.message_type.file_type import Audio_Files

NOTIFY_URL = 'https://notify-api.line.me/api/notify'
NOTIFY_STATUS_URL = 'https://notify-api.line.me/api/status'
LINE_BOT_URL = 'https://api.line.me/v2/bot'
LINE_CONTENT_URL = 'https://api-data.line.me/v2/bot'

class Voice_File():
    def __init__(self,url:str,second:float) -> None:
        """
        Discordの音声ファイルのURLと秒数を格納するクラス

        param
        url:str
        音声ファイルのURL

        second:float
        音声ファイルの秒数(秒)
        """
        self.url = url
        self.second = second

# LINEのgetリクエストを行う
async def line_get_request(url: str, token: str) -> json:
    """
    GETリクエストを送る。
    param
    url:str
    リクエストを送るURL

    token:str
    LINEのトークン

    return
    resp.json:json
    レスポンスを示すjsonファイル。
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url = url,
            headers = {'Authorization': 'Bearer ' + token}
        ) as resp:
            return await resp.json()

# LINEのpostリクエストを行う
async def line_post_request(url: str, headers: dict, data: dict) -> json:
    """
    POSTリクエストを送る。
    param
    url:str
    リクエストを送るURL

    headers:dict
    リクエストを送るヘッダ

    data:dict
    リクエスト先に送るパラメータ

    return
    resp.json:json
    レスポンスを示すjsonファイル。
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url = url,
            headers = headers,
            data = data
        ) as resp:
            return await resp.json()

class LineBotAPI:
    def __init__(
        self, 
        notify_token: str, 
        line_bot_token: str, 
        line_group_id: str
    ) -> None:
        """
        LINEBotのオブジェクト

        param
        notify_token: str
        LINE Notifyのトークン

        line_bot_token: str 
        LINEBotのトークン

        line_group_id: str
        LINEグループのid
        """
        self.notify_token = notify_token
        self.line_bot_token = line_bot_token
        self.line_group_id = line_group_id
        self.loop = asyncio.get_event_loop()

    # LINE Notifyでテキストメッセージを送信
    async def push_message_notify(self, message: str) -> json:
        """
        LINE Notifyでテキストメッセージを送信

        param
        message:str
        送信するテキストメッセージ

        return
        resp.json:json
        レスポンス
        """
        data = {'message': f'message: {message}'}
        return await line_post_request(
            url = NOTIFY_URL, 
            headers = {'Authorization': f'Bearer {self.notify_token}'}, 
            data = data
        )
        
    # LINE Notifyで画像を送信
    async def push_image_notify(self, message: str, image_url: str) -> json:
        """
        LINE Notifyで画像を送信

        param
        message:str
        送信するテキストメッセージ

        image_url:str
        送信する画像のURL

        return
        resp.json:json
        レスポンス
        """
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

    # LINE Messageing APIでテキストメッセージを送信
    async def push_message(self,message_text:str) -> json:
        """
        LINE Messageing APIでテキストメッセージを送信

        param
        message:str
        送信するテキストメッセージ

        return
        resp.json:json
        レスポンス
        """
        data = {
            'to':self.line_group_id,
            'messages':[
                {
                    'type':'text',
                    'text':message_text
                }
            ]
        }
        return await line_post_request(
            url = LINE_BOT_URL + "/message/push",
            headers = {
                'Authorization': 'Bearer ' + self.line_bot_token,
                'Content-Type': 'application/json'
            },
            data = json.dumps(data)
        )

    # LINE Messageing APIで画像を送信
    async def push_image(self,message_text:str,image_urls:List[str]) -> json:
        """
        LINE Messageing APIで画像を送信

        param
        message_text:str
        送信するテキストメッセージ

        image_urls:List[str]
        送信する画像のURL(複数)

        return
        resp.json:json
        レスポンス
        """
        data = [
            {
                'type':'text',
                'text':message_text
            }
        ]

        for image_url in image_urls:
            data.append({
                'type':'image',
                'imageThumbnail': f'{image_url}',
                'imageFullsize': f'{image_url}',
            })

        datas = {
            'to':self.line_group_id,
            'messages':data
        }

        return await line_post_request(
            url = LINE_BOT_URL + "/message/push",
            headers = {
                'Authorization': 'Bearer ' + self.line_bot_token,
                'Content-Type': 'application/json'
            },
            data = json.dumps(datas)
        )

    # 動画の送信(動画のみ)
    async def push_movie(self, preview_image: str, movie_urls: List[str]) -> json:
        """
        LINEBotで動画の送信(動画のみ)

        param
        preview_image:str
        プレビュー画像のURL

        movie_urls:List[str]
        動画のURL(複数)

        return
        resp.json:json
        レスポンス
        """
        data = []
        # 動画を1個ずつ格納
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
    
    async def push_voice(self,voice_file:List[Voice_File]) -> Dict:
        """
        LINEBotで音声の送信

        param
        voice_file:List[Voice_File]
        送信する音声ファイルのクラス

        return
        Dict
        レスポンス
        """
        data = []
        for voice in voice_file:
            data.append({
                'type':'audio',
                'originalContentUrl':voice.url,
                'duration':int(voice.second * 1000)
            })
        datas = {
            'to': self.line_group_id,
            'messages': data
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
        """
        送ったメッセージ数を取得
        
        return
        totalUsage:int
        送ったメッセージの総数
        """
        r = await line_get_request(
            LINE_BOT_URL + "/message/quota/consumption",
            self.line_bot_token
        )
        return int(r["totalUsage"])

    # LINE Notifyのステータスを取得
    async def notify_status(self) -> Response:
        """
        LINE Notifyのステータスを取得

        return
        resp:Response
        レスポンス
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = NOTIFY_STATUS_URL,
                headers = {'Authorization': 'Bearer ' + self.notify_token}
            ) as resp:
                return resp

    # LINE Notifyの1時間当たりの上限を取得
    async def rate_limit(self) -> int:
        """
        LINE Notifyの1時間当たりの上限を取得

        return
        X-RateLimit-Limit:int
        リクエスト上限数
        """
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-Limit')
        return int(ratelimit)

    # LINE Notifyの1時間当たりの残りの回数を取得
    async def rate_remaining(self) -> int:
        """
        LINE Notifyの1時間当たりの残りの回数を取得

        return
        X-RateLimit-Remaining:int
        残りリクエスト数
        """
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-Remaining')
        return int(ratelimit)

    # LINE Notifyの1時間当たりの画像送信上限を取得
    async def rate_image_limit(self) -> int:
        """
        LINE Notifyの1時間当たりの画像送信上限を取得

        return
        X-RateLimit-ImageLimit:int
        画像送信上限数
        """
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-ImageLimit')
        return int(ratelimit)

    # LINE Notifyの1時間当たりの残り画像送信上限を取得
    async def rate_image_remaining(self) -> int:
        """
        LINE Notifyの1時間当たりの残り画像送信上限を取得

        return
        X-RateLimit-ImageRemaining:int
        残り画像送信上限数
        """
        resp = await self.notify_status()
        ratelimit = resp.headers.get('X-RateLimit-ImageRemaining')
        return int(ratelimit)

    # 友達数、グループ人数をカウント
    async def friend(self) -> str:
        """
        友達数、グループ人数を数える

        return
        count or followers:int
        友達数、またはグループ人数
        """
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
    async def pushlimit(self) -> str:
        """
        当月に送信できるメッセージ数の上限目安を取得
        23年6月以降は200になる

        return
        value:int
        メッセージの上限目安(基本1000,23年6月以降は200)
        """
        r = await line_get_request(
            LINE_BOT_URL + "/message/quota",
            self.line_bot_token
        )
        return r["value"]


    # LINEのユーザプロフィールから名前を取得
    async def get_proflie(self, user_id: str) -> Profile:
        """
        LINEのユーザプロフィールから名前を取得

        param
        user_id:str
        LINEのユーザーid

        return
        profile:Profile
        LINEユーザーのプロフィールオブジェクト
        """
        # グループIDが有効かどうか判断
        try:
            r = await line_get_request(
                LINE_BOT_URL + f"/group/{self.line_group_id}/member/{user_id}",
                self.line_bot_token,
            )
            r["user_id"]
        # グループIDが無効の場合、友達から判断
        except KeyError:
            r = await line_get_request(
                LINE_BOT_URL + f"/profile/{user_id}",
                self.line_bot_token,
            )
        return await Profile.new_from_json_dict(data=r)

    # LINEから画像データを取得し、Gyazoにアップロード
    async def image_upload(self, message_id: int) -> GyazoJson:
        """
        LINEから画像データを取得し、Gyazoにアップロードする

        param
        message_id:int
        LINEのメッセージのid

        return
        gayzo:GyazoJson
        Gyazoの画像のオブジェクト
        """
        # 画像のバイナリデータを取得
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url = LINE_CONTENT_URL + f'/message/{message_id}/content',
                    headers={
                        'Authorization': 'Bearer ' + self.line_bot_token
                    }
            ) as bytes:
                image_bytes = await bytes.read()

                # Gyazoにアップロードする
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url = 'https://upload.gyazo.com/api/upload',
                        headers={
                            'Authorization': 'Bearer ' + os.environ['GYAZO_TOKEN'],
                        },
                        data={
                            'imagedata': image_bytes
                        }
                    ) as gyazo_image:
                        return await GyazoJson.new_from_json_dict(await gyazo_image.json())
        
    # LINEから受け取った動画を保存し、YouTubeに限定公開でアップロード
    async def movie_upload(self, message_id: int, display_name: str) -> str:
        """
        LINEから受け取った動画を保存し、YouTubeに限定公開でアップロード

        param
        message_id:int
        LINEのメッセージのid

        display_name:str
        LINEのユーザー名

        return
        youtube_id:str
        YouTubeの動画id
        """
        # 動画のバイナリデータを取得
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url = LINE_CONTENT_URL + f'/message/{message_id}/content',
                    headers={
                        'Authorization': 'Bearer ' + self.line_bot_token
                    }
            ) as bytes:

                video_bytes = await bytes.read()

                youtube_video = YouTubeUpload(
                    title=f"{display_name}からの動画",
                    description="LINEからの動画",
                    privacy_status="unlisted"
                )

                youtube = await youtube_video.get_authenticated_service()

                return await youtube_video.byte_upload(
                    video_bytes=io.BytesIO(video_bytes),
                    youtube=youtube
                )
    
    #
    async def voice_get(self ,message_id: int) -> Audio_Files:
        """"""
        # 音声のバイナリデータを取得
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url = LINE_CONTENT_URL + f'/message/{message_id}/content',
                    headers={
                        'Authorization': 'Bearer ' + self.line_bot_token
                    }
            ) as bytes:

                voice_bytes = await bytes.read()

                # アップロードするファイルを指定する
                return Audio_Files(
                    byte=io.BytesIO(voice_bytes),
                    filename='line_audio'
                )



if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    #line = Notify(notify_token, line_bot_api, line_group_id)

    #start = time.time()
    token = os.environ['6_NOTIFY_TOKEN']
    resp = requests.get('https://notify-api.line.me/api/status', headers={'Authorization': f'Bearer {token}'})
    ratelimit = resp.headers.get("X-RateLimit-Limit")
    print(ratelimit)