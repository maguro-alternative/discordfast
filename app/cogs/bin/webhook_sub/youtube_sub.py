import aiohttp

from dotenv import load_dotenv
load_dotenv()

import os

from datetime import datetime
from typing import Dict

from model_types.table_type import WebhookSet
from model_types.youtube_api_type import YouTubeChannelList,YouTubeChannelInfo
from core.db_pickle import DB

async def youtube_subsc(
    webhook:WebhookSet,
    webhook_url:str,
    table_name:str
) -> None:
    """
    YouTubeの最新動画を取得し、Webhookで投稿する

    pream:
    webhook:Dict
        webhookの情報を示す辞書型オブジェクト
    webhook_url
        webhookのurl
    table_name
        webhookの情報が登録されているテーブル名
    """
    youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
    channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={webhook.subscription_id}&key={youtube_api_key}"
    new_videos_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={webhook.subscription_id}&order=date&type=video&key={youtube_api_key}&maxResults=5"

    # 最終更新日を格納
    created_at = webhook.created_at
    last_upload_time = datetime.strptime(
        created_at,
        '%a %b %d %H:%M:%S %z %Y'
    )

    async with aiohttp.ClientSession() as sessions:
        async with sessions.get(
            url=new_videos_url
        ) as resp:
            new_videos_info:dict = await resp.json()
            youtube_info = YouTubeChannelList(**new_videos_info)

            # 最新動画を取得
            videos_items = youtube_info.items

        for i,item in enumerate(videos_items):
            upload_time_str = item.snippet.publishTime
            upload_time = datetime.strptime(
                upload_time_str,
                '%Y-%m-%dT%H:%M:%SZ'
            )
            # 更新があった場合
            if last_upload_time < upload_time:
                if not bool('channel_info' in locals()):
                    async with sessions.get(
                        url=channel_url
                    ) as re:
                        channel:dict = await re.json()
                        channel_info = YouTubeChannelInfo(**channel)
                        # チャンネルの基本情報を取得
                        channel_item = channel_info.items[0]
                        # チャンネルのアイコンを取得
                        channel_icon_url:str = channel_item.snippet.thumbnails.high.url
                        # チャンネル名を取得
                        channel_title = channel_item.snippet.title

                # YouTube動画のタイトル
                video_title = item.snippet.title
                # YouTube動画のURL
                video_url = f"https://youtu.be/{item.id.videoId}"

                if len(webhook.mention_roles) > 0:
                    # メンションするロールの取り出し
                    mentions = [
                        f"<@&{int(role_id)}> "
                        for role_id in webhook.mention_roles
                    ]
                    text = " ".join(mentions) + " "

                if len(webhook.mention_members) > 0:
                    members = [
                        f"<@{int(member_id)}> "
                        for member_id in webhook.mention_members
                    ]
                    text = " ".join(members) + " "

                text += '\n' + video_title + '\n' + video_url

                # webhookに投稿
                async with sessions.post(
                    url=webhook_url,
                    data={
                        'username':channel_title,
                        'avatar_url':channel_icon_url,
                        'content':text
                    }
                ) as re:
                    if i == len(videos_items)-1:
                        # データベースに接続し、最終更新日を更新
                        if DB.conn == None:
                            await DB.connect()
                        await DB.update_row(
                            table_name=table_name,
                            row_values={
                                'created_at':upload_time.strftime('%a %b %d %H:%M:%S %z %Y')
                            },
                            where_clause={
                                'uuid':webhook.uuid
                            }
                        )