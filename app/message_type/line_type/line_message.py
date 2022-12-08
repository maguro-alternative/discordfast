import json
import requests
import datetime
import calendar
import os
import math
import asyncio
import time
from functools import partial

import subprocess
from typing import List

from dotenv import load_dotenv
load_dotenv()
try:
    from message_type.line_type.class_type import Profile,GyazoJson
except:
    from app.message_type.line_type.class_type import Profile,GyazoJson

async def line_req(url: str, token: str) -> json:
    loop = asyncio.get_event_loop()
    r = (
        await loop.run_in_executor(
            None,
            partial(
                requests.get,
                url=url,
                headers={
                    'Authorization': 'Bearer ' + token
                }
            )
        )
    )
    return r.json()

class DayInfo:
    # 現在の時刻
    def today_time(self):
        return datetime.datetime.now()

    # 現在の日付
    def today(self):
        return datetime.datetime.now().day

    # 今月末の日
    def endmonth(self):
        return calendar.monthrange(datetime.datetime.now().year, datetime.datetime.now().month)[1]


class BotInfo(DayInfo):
    def __init__(self, line_bot_token: str, line_group_id: str) -> None:
        self.line_group_id = line_group_id
        self.line_bot_token = line_bot_token

    async def totalpush(self) -> int:
        return await line_req(
            "https://api.line.me/v2/bot/message/quota/consumption",
            self.line_bot_token
        )["totalUsage"]

    # 友達数、グループ人数をカウント
    async def friend(self):
        # グループIDが有効かどうか判断
        try:
            r = await line_req(
                "https://api.line.me/v2/bot/group/" + self.line_group_id + "/members/count",
                self.line_bot_token,
            )
            return r["count"]
        # グループIDなしの場合、友達数をカウント
        except KeyError:
            # 日付が変わった直後の場合、前日を参照
            if datetime.datetime.now().strftime('%H') == '00':
                url = "https://api.line.me/v2/bot/insight/followers?date=" + (
                            datetime.date.today() + datetime.timedelta(days=-1)).strftime('%Y%m%d')
            else:
                url = "https://api.line.me/v2/bot/insight/followers?date=" + datetime.date.today().strftime('%Y%m%d')
            r = await line_req(
                url,
                self.line_bot_token,
            )
            return r["followers"]
        #print(count)
        #return count

    # 当月に送信できるメッセージ数の上限目安を取得(基本1000,23年6月以降は200)
    async def pushlimit(self):
        r = await line_req(
            "https://api.line.me/v2/bot/message/quota",
            self.line_bot_token
        )
        return r["value"]


class AfterTotal(BotInfo):
    def __init__(self, line_bot_token: str, line_group_id: str) -> None:
        super().__init__(line_bot_token, line_group_id)

    # 0+1 297+11=308
    async def aftertotal(self) -> int:
        """
        aftertotal

        当月分のプッシュ数に友達数(1回送信した)を足した値
        送信後の値になる

        戻り値例:int
        メッセージ送信数=297件
        友達数=11人

        297+11=308
        """
        return await super().totalpush() + await super().friend()


class BotPush(AfterTotal):
    def __init__(self, line_bot_token: str, line_group_id: str) -> None:
        super().__init__(line_bot_token, line_group_id)

    # 1000/30=33.3333
    async def onedaypush(self) -> float:
        """
        onedaypush

        当月分のメッセージ上限を月末の日付で割った値

        戻り値例:float
        メッセージ上限=1000件
        月末の日付=30日

        1000/30=33.333...
        """
        return await super().pushlimit() / super().endmonth()

    # 0/1 297/17=17.4705
    async def todaypush(self) -> float:
        """
        todaypush

        当月分のプッシュ数を現在の日付で割った値
        また、この時点では送信前の値となる

        戻り値例:float
        メッセージ送信数=297件
        現在の日付=17日

        297/17=17.4705
        """
        return await super().totalpush() / super().today()

    # (0+1)/1 (297+11)/17=18.117
    async def afterpush(self) -> float:
        """
        afterpush
        当月分のプッシュ数に友達数(1回送信した)を足して、現在の日付で割った値
        送信後の値になる
        戻り値例:float
        メッセージ送信数=297件
        友達数=11人
        現在の日付=17日
        (297+11)/17=18.117
        """
        return await super().aftertotal() / super().today()


class DaysGet(BotPush):
    def __init__(self, line_bot_token: str, line_group_id: str) -> None:
        super().__init__(line_bot_token, line_group_id)

    # 1-0 18.117-17.4705=0.6465
    async def consumption(self) -> float:
        """
        consumption
        1回送信するたびに消費される上限数
        戻り値例:float
        メッセージ送信数=297件
        友達数=11人
        現在の日付=17日
        当月分のプッシュ数に友達数を足して、現在の日付で割った値=(297+11)/17=18.117
        当月分のプッシュ数を現在の日付で割った値=297/17=17.4705
        18.117-17.4705=0.6465
        """
        return await super().afterpush() - await super().todaypush()

    # (33.333-0)/1
    async def daylimit(self) -> int:
        """
        daylimit
        消費される上限数から本日分の上限を計算(小数点以下切り上げ)
        戻り値例:int
        メッセージ送信数=297件
        友達数=11人
        現在の日付=17日
        月末の日付=30日
        当月分のメッセージ上限を月末の日付で割った値=1000/30=33.333
        当月分のプッシュ数に友達数を足して、現在の日付で割った値=(297+11)/17=18.117
        1回送信するたびに消費される上限数=18.117-17.4705=0.6465
        (33.333-18.117)/0.6465=23.53=24
        """
        return math.ceil(
            (
                    await super().onedaypush() - await super().afterpush()
            ) / await super().afterpush() - await super().todaypush()
        )

    # 33.333/1
    async def templelimit(self) -> int:
        """
        templelimit
        1日当たりの上限を計算(小数点以下切り上げ)
        戻り値例:int
        友達数=11人
        月末の日付=30日
        当月分のメッセージ上限を月末の日付で割った値=1000/30=33.333
        33.333/11=3.0303=4
        """
        return math.ceil(
            await super().onedaypush() / await super().friend()
        )


class LineMessageAPI(DaysGet):
    def __init__(self, line_bot_token: str, line_group_id: str) -> None:
        self.line_group_id = line_group_id
        self.line_bot_token = line_bot_token
        super().__init__(line_bot_token, line_group_id)

    # LINEのユーザプロフィールから名前を取得
    async def get_proflie(self, user_id: str):# -> Profile:
        # グループIDが有効かどうか判断
        try:
            r = await line_req(
                f"https://api.line.me/v2/bot/group/{self.line_group_id}/member/{user_id}",
                self.line_bot_token,
            )
        # グループIDが無効の場合、友達から判断
        except KeyError:
            r = await line_req(
                f"https://api.line.me/v2/bot/profile/{user_id}",
                self.line_bot_token,
            )
        return await Profile.new_from_json_dict(data=r)

    # LINEから画像データを取得し、Gyazoにアップロード
    async def get_image_byte(self, message_id: int):
        # 画像のバイナリデータを取得
        image_bytes = requests.get(
            f'https://api-data.line.me/v2/bot/message/{message_id}/content',
            headers={
                'Authorization': 'Bearer ' + self.line_bot_token
            }
        ).content
        # Gyazoにアップロードする
        gyazo_image = requests.post(
            "https://upload.gyazo.com/api/upload",
            headers={
                'Authorization': 'Bearer ' + os.environ['GYAZO_TOKEN']
            },
            files={
                'imagedata': image_bytes
            }
        ).json()

        return await GyazoJson.new_from_json_dict(gyazo_image)
        # 受け取ったjsonから画像のURLを生成
        # return f"https://i.gyazo.com/{gyazo_image['image_id']}.{gyazo_image['type']}"

    # LINEから受け取った動画を保存し、YouTubeに限定公開でアップロード
    async def movie_upload(self, message_id: int, display_name: str):
        # 動画のバイナリデータを取得
        movies_bytes = requests.get(
            f'https://api-data.line.me/v2/bot/message/{message_id}/content',
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


class Notify(LineMessageAPI):
    def __init__(self, notify_token: str, line_bot_token: str, line_group_id: str) -> None:
        self.notify_url = 'https://notify-api.line.me/api/notify'
        self.header = {
            'Authorization': f'Bearer {notify_token}'
        }
        super().__init__(line_bot_token, line_group_id)

    # LINE Notifyでテキストメッセージを送信
    async def push_message_notify(self, message: str):
        data = {'message': f'message: {message}'}
        return requests.post(url=self.notify_url, headers=self.header, data=data)

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
        return requests.post(url=self.notify_url, headers=self.header, data=data)

    # 動画の送信(動画のみ)
    async def push_movie(self, preview_image: str, movie_urls: List[str]):
        data = []
        if len(preview_image) == 0:
            preview_image = ""
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
            url="https://api.line.me/v2/bot/message/push",
            headers={
                'Authorization': 'Bearer ' + self.line_bot_token,
                'Content-Type': 'application/json'
            },
            data=json.dumps(datas)
        )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    #line = Notify(notify_token, line_bot_api, line_group_id)

    start = time.time()