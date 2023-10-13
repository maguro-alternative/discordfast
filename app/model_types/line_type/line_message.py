import json
from requests import Response

import datetime

import io
import asyncio

import aiohttp
from typing import List,Dict

try:
    from model_types.youtube_upload import YouTubeUpload
    from model_types.file_type import ImageFiles,AudioFiles
    from model_types.line_type.line_type import (
        LineBotConsumption,
        LineGroupCount,
        LineBotFriend,
        LineBotQuota,
        LineBotInfo
    )
    from model_types.line_type.line_oauth import LineProfile
except ModuleNotFoundError:
    from app.model_types.youtube_upload import YouTubeUpload
    from app.model_types.file_type import ImageFiles,AudioFiles
    from app.model_types.line_type.line_type import (
        LineBotConsumption,
        LineGroupCount,
        LineBotFriend,
        LineBotQuota,
        LineBotInfo
    )
    from app.model_types.line_type.line_oauth import LineProfile

NOTIFY_URL = 'https://notify-api.line.me/api/notify'
NOTIFY_STATUS_URL = 'https://notify-api.line.me/api/status'
LINE_BOT_URL = 'https://api.line.me/v2/bot'
LINE_CONTENT_URL = 'https://api-data.line.me/v2/bot'

class VoiceFile:
    """
    Discordの音声ファイルのURLと秒数を格納するクラス

    param:
    url     :str
        音声ファイルのURL

    second  :float
        音声ファイルの秒数(秒)
    """
    def __init__(self,url:str,second:float) -> None:
        self.url = url
        self.second = second

class NotifyStates:
    """
    LINE Notifyのステータス
    ヘッダーから読み取る

    param:
    notify:Response
        LINE Notifyのステータスのレスポンス
    """
    def __init__(
        self,
        notify:Response
    ) -> None:
        """
        self.rate_limit         :int
            1時間当たりのメッセージ送信上限
        self.rate_remaining     :int
            残りのメッセージ送信上限
        self.image_limit        :int
            1時間当たりの画像送信上限
        self.image_remaining    :int
            残り画像送信上限
        self.message            :str
            エラーメッセージ
        self.states             :int
            ステータスコード
        """
        self.rate_limit = int(notify.headers.get('X-RateLimit-Limit'))
        self.rate_remaining = int(notify.headers.get('X-RateLimit-Remaining'))
        self.image_limit = int(notify.headers.get('X-RateLimit-ImageLimit'))
        self.image_remaining = int(notify.headers.get('X-RateLimit-ImageRemaining'))
        self.message = notify.headers.get('message')
        self.status = notify.headers.get('status',default=200)


# LINEのgetリクエストを行う
async def line_get_request(
    url: str,
    token: str
) -> Dict:
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
async def line_post_request(
    url: str,
    headers: Dict,
    data: Dict
) -> Dict:
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
    def __init__(
        self,
        notify_token: str,
        line_bot_token: str,
        line_group_id: str
    ) -> None:
        self.notify_token = notify_token
        self.line_bot_token = line_bot_token
        self.line_group_id = line_group_id
        self.loop = asyncio.get_event_loop()

    # LINE Notifyでテキストメッセージを送信
    async def push_message_notify(self, message: str) -> Dict:
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
    async def push_image_notify(
        self,
        message: str,
        image_url: str
    ) -> Dict:
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
    async def push_message(self,message_text:str) -> Dict:
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
            url=f"{LINE_BOT_URL}/message/push",
            headers={
                'Authorization': f'Bearer {self.line_bot_token}',
                'Content-Type': 'application/json'
            },
            data=json.dumps(data)
        )

    # LINE Messageing APIで画像を送信
    async def push_image(
        self,
        message_text:str,
        image_urls:List[str]
    ) -> Dict:
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
            url=f"{LINE_BOT_URL}/message/push",
            headers={
                'Authorization': f'Bearer {self.line_bot_token}',
                'Content-Type': 'application/json'
            },
            data=json.dumps(datas)
        )

    # 動画の送信(動画のみ)
    async def push_movie(
        self,
        preview_image: str,
        movie_urls: List[str]
    ) -> Dict:
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
            url=f"{LINE_BOT_URL}/message/push",
            headers={
                'Authorization': f'Bearer {self.line_bot_token}',
                'Content-Type': 'application/json'
            },
            data=json.dumps(datas)
        )

    async def push_voice(
        self,
        VoiceFile:List[VoiceFile]
    ) -> Dict:
        """
        LINEBotで音声の送信

        param
        VoiceFile:List[VoiceFile]
            送信する音声ファイルのクラス

        return
        Dict
            レスポンス
        """
        data = []
        for voice in VoiceFile:
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
            url=f"{LINE_BOT_URL}/message/push",
            headers={
                'Authorization': 'Bearer {self.line_bot_token}',
                'Content-Type': 'application/json'
            },
            data=json.dumps(datas)
        )

    async def get_bot_info(self) -> LineBotInfo:
        """
        LINE Botのプロフィール情報を取得

        Returns:
        LineBotInfo:
            LINEBotのプロフィール情報
        """
        r = await line_get_request(
            url=f"{LINE_BOT_URL}/info",
            token=self.line_bot_token
        )
        i = LineBotInfo(**r)
        return i

    # 送ったメッセージ数を取得
    async def totalpush(self) -> LineBotConsumption:
        """
        送ったメッセージ数を取得

        return
        totalUsage:int
            送ったメッセージの総数
        """
        r = await line_get_request(
            url=f"{LINE_BOT_URL}/message/quota/consumption",
            token=self.line_bot_token
        )
        return LineBotConsumption(**r)

    # LINE Notifyのステータスを取得
    async def notify_status(self) -> NotifyStates:
        """
        LINE Notifyのステータスを取得

        return
        resp:Response
            レスポンス
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=NOTIFY_STATUS_URL,
                headers={'Authorization': 'Bearer ' + self.notify_token}
            ) as resp:
                return NotifyStates(notify=resp)

    async def group_user_count(self) -> LineGroupCount:
        """
        グループ人数を数える

        return
        LineGroupCount
            グループ人数
        """
        r = await line_get_request(
            url=f"{LINE_BOT_URL}/group/{self.line_group_id}/members/count",
            token=self.line_bot_token
        )
        return LineGroupCount(**r)

    async def friend_count(self) -> LineBotFriend:
        """
        友達数を数える

        return
        LineBotFriend
            友達数
        """
        r = await line_get_request(
            url=f"{LINE_BOT_URL}/group/{self.line_group_id}/members/count",
            token=self.line_bot_token
        )
        return LineBotFriend(**r)

    # 友達数、グループ人数をカウント
    async def group_or_friend_count(self) -> int:
        """
        友達数、グループ人数を数える

        return
        count or followers:int
            友達数、またはグループ人数
        """
        # グループIDが有効かどうか判断
        r = await line_get_request(
            url=f"{LINE_BOT_URL}/group/{self.line_group_id}/members/count",
            token=self.line_bot_token
        )
        c = LineGroupCount(**r)
        # グループIDなしの場合、友達数をカウント
        if c.count == None:
            # 日付が変わった直後の場合、前日を参照
            if datetime.datetime.now().strftime('%H') == '00':
                before_day = datetime.date.today() + datetime.timedelta(days=-1)
                url = f"{LINE_BOT_URL}/insight/followers?date={before_day.strftime('%Y%m%d')}"
            else:
                url = f"{LINE_BOT_URL}/insight/followers?date={datetime.date.today().strftime('%Y%m%d')}"
            r = await line_get_request(
                url=url,
                token=self.line_bot_token,
            )
            f = LineBotFriend(**r)
            return f.followers
        return c.count

    # 当月に送信できるメッセージ数の上限目安を取得(基本1000,23年6月以降は200)
    async def pushlimit(self) -> LineBotQuota:
        """
        当月に送信できるメッセージ数の上限目安を取得
        23年6月以降は200になる

        return
        LineBotQuota
            メッセージの上限目安(基本1000,23年6月以降は200)
        """
        r = await line_get_request(
            url=f"{LINE_BOT_URL}/message/quota",
            token=self.line_bot_token
        )
        v = LineBotQuota(**r)
        return v


    # LINEのユーザプロフィールから名前を取得
    async def get_proflie(self, user_id: str) -> LineProfile:
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
        r = await line_get_request(
            url=f"{LINE_BOT_URL}/group/{self.line_group_id}/member/{user_id}",
            token=self.line_bot_token,
        )

        # グループIDが無効の場合、友達から判断
        if r.get('message') != None:
            r = await line_get_request(
                url=f"{LINE_BOT_URL}/profile/{user_id}",
                token=self.line_bot_token,
            )
        return LineProfile(**r)

    # LINEから画像データを取得
    async def image_upload(self, message_id: int) -> ImageFiles:
        """
        LINEから画像データを取得し、discordにアップロードする

        param
        message_id:int
            LINEのメッセージのid

        return
        ImageFiles
            画像のオブジェクト
        """
        # 画像のバイナリデータを取得
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f'{LINE_CONTENT_URL}/message/{message_id}/content',
                    headers={
                        'Authorization': 'Bearer ' + self.line_bot_token
                    }
            ) as bytes:
                image_bytes = await bytes.read()

                return ImageFiles(
                    byte=image_bytes,
                    filename='line_image'
                )

    # LINEから受け取った動画を保存し、YouTubeに限定公開でアップロード
    async def movie_upload(
        self,
        message_id: int,
        display_name: str
    ) -> str:
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
                    url=f'{LINE_CONTENT_URL}/message/{message_id}/content',
                    headers={
                        'Authorization': f'Bearer {self.line_bot_token}'
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

    # LINEから受け取った音声データを取得し、Discordにアップロード
    async def voice_get(self ,message_id: int) -> AudioFiles:
        """
        LINEから受け取った音声データを取得し、Discordにアップロード

        param:
        message_id:int
            LINEのメッセージのid

        return
        Audio_File
            アップロードする音声データのクラス
        """
        # 音声のバイナリデータを取得
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    url=f'{LINE_CONTENT_URL}/message/{message_id}/content',
                    headers={
                        'Authorization': f'Bearer {self.line_bot_token}'
                    }
            ) as bytes:

                voice_bytes = await bytes.read()

                # アップロードするファイルを指定する
                return AudioFiles(
                    byte=voice_bytes,
                    filename='line_audio'
                )
