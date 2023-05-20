from discord.ext import commands,tasks

import aiofiles
import aiohttp

import feedparser
from bs4 import BeautifulSoup

try:
    # Botのみ起動の場合
    from app.core.start import DBot
    from app.cogs.bin.tweetget import Twitter_Get_Tweet
except ModuleNotFoundError:
    from core.start import DBot
    from cogs.bin.tweetget import Twitter_Get_Tweet

from dotenv import load_dotenv
load_dotenv()

import os
import io
import pickle
from datetime import datetime,timezone
from typing import Dict,List

from base.database import PostgresDB
from base.aio_req import (
    pickle_read,
    pickle_write
)

USER = os.getenv('PGUSER')
PASSWORD = os.getenv('PGPASSWORD')
DATABASE = os.getenv('PGDATABASE')
HOST = os.getenv('PGHOST')
db = PostgresDB(
    user=USER,
    password=PASSWORD,
    database=DATABASE,
    host=HOST
)

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]


class Webhook_Post(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot
        self.webhook_signal.start()

    @tasks.loop(seconds=90)
    async def webhook_signal(self):
        # Botが起動しないとサーバを取得できない
        # なので起動時の読み込みでは機能しない
        for guild in self.bot.guilds:
            table_name = f"webhook_{guild.id}"
            # 読み取り
            webhook_fetch:List[Dict] = await pickle_read(filename=table_name)

            # 登録してあるwebhookを一つ一つ処理
            for webhook in webhook_fetch:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url=f"{DISCORD_BASE_URL}/webhooks/{webhook.get('webhook_id')}",
                        headers={
                            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                        }
                    ) as resp:
                        # 使用するWebHookの情報を取得
                        webhook_obj = await resp.json()
                        webhook_url = f"{DISCORD_BASE_URL}/webhooks/{webhook.get('webhook_id')}/{webhook_obj.get('token')}"

                        # twitterの場合
                        if webhook.get('subscription_type') == 'twitter':
                            await twitter_subsc(
                                webhook=webhook,
                                webhook_url=webhook_url,
                                table_name=table_name
                            )

                        # niconicoの場合
                        if webhook.get('subscription_type') == 'niconico':
                            await niconico_subsc(
                                webhook=webhook,
                                webhook_url=webhook_url,
                                table_name=table_name
                            )


async def twitter_subsc(
    webhook:Dict,
    webhook_url:str,
    table_name:str
) -> None:
    """
    twitterの最新ツイートを取得し、WebHookで投稿する

    pream:
    webhook:Dict
        webhookの情報を示す辞書型オブジェクト
    webhook_url
        webhookのurl
    table_name
        webhookの情報が登録されているテーブル名
    """
    # クラスを宣言
    twitter = Twitter_Get_Tweet(
        screen_name=webhook.get('subscription_id'),
        search_word=""
    )
    
    # 最新ツイートと更新日時を取得(ない場合はそのまま)
    tweetlist, create_at = await twitter.mention_tweet_make(
        webhook_fetch=webhook
    )
    
    async with aiohttp.ClientSession() as sessions:
        # 取得したツイートを一つ一つwebhookで送信
        for tweet in tweetlist:
            # 最初の要素の場合
            if tweet == tweetlist[0]:
                # アイコンurl,ユーザ名を取得
                image_url, username = await twitter.get_image_and_name()
            async with sessions.post(
                url=webhook_url,
                data={
                    'username':username,
                    'avatar_url':image_url,
                    'content':tweet
                }
            ) as re:
                # 最後の要素の場合
                if tweet == tweetlist[-1]:
                    # データベースに接続し、最終更新日を更新
                    await db.connect()

                    await db.update_row(
                        table_name=table_name,
                        row_values={
                            'created_at':create_at
                        },
                        where_clause={
                            'uuid':webhook.get('uuid')
                        }
                    )
                    table_fetch = await db.select_rows(
                        table_name=table_name,
                        columns=[],
                        where_clause={}
                    )

                    await db.disconnect()

                    # pickleファイルに書き込み
                    await pickle_write(
                        filename=table_name,
                        table_fetch=table_fetch
                    )

                

async def niconico_subsc(
    webhook:Dict,
    webhook_url:str,
    table_name:str
) -> None:
    """
    niconicoの最新動画を取得し、webhookに送信

    param:
    webhook:Dict
        webhookの情報を示す辞書型オブジェクト
    webhook_url
        webhookのurl
    table_name
        webhookの情報が登録されているテーブル名
    """
    # rssのurl
    niconico_rss_url = f"https://www.nicovideo.jp/user/{webhook.get('subscription_id')}/video?rss=2.0"
    # rssを取得し展開
    niconico = feedparser.parse(
        url_file_stream_or_string=niconico_rss_url
    )
    
    # 最終更新日を格納
    created_at = webhook.get('created_at')
    update_at = ''


    async with aiohttp.ClientSession() as sessions:
        upload_flag = False
        mention_flag = True
        # 最新の動画を一つ一つ処理
        for entry in niconico.entries:
            # Webhookに最後にアップロードした時刻
            strTime = datetime.strptime(
                created_at, 
                '%a %b %d %H:%M:%S %z %Y'
            )
            # 動画の投稿時刻
            lastUpdate = datetime.strptime(
                entry.published,
                '%a, %d %b %Y %H:%M:%S %z'
            )
            # 最初の要素の場合(最新の要素)
            if entry == niconico.entries[0]:
                # 現在時刻の取得
                now_time = datetime.now(timezone.utc)
                update_at = now_time.strftime('%a %b %d %H:%M:%S %z %Y')
            
            # htmlとしてパース
            soup = BeautifulSoup(entry.summary, 'html.parser')
            
            # 最新の動画が投稿されていた場合
            if strTime < lastUpdate:
                # すべてのimgタグのsrcを取得する
                img_src_list = [
                    img['src'] 
                    for img in soup.find_all('img')
                ]

                text = ""
                if mention_flag:
                    # メンションするロールの取り出し
                    mentions = [
                        f"<@&{int(role_id)}> " 
                        for role_id in webhook.get('mention_roles')
                    ]
                    members = [
                        f"<@{int(member_id)}> " 
                        for member_id in webhook.get('mention_members')
                    ]
                    text = " ".join(mentions) + " " + " ".join(members)

                # タイトルとリンクをテキストにする
                text += f' {entry.title}\n{entry.link}' 
            
                # webhookに投稿
                async with sessions.post(
                    url=webhook_url,
                    data={
                        'username':niconico.feed.title,
                        'avatar_url':img_src_list[0],
                        'content':text
                    }
                ) as re:
                    upload_flag = True

        # 投稿があった場合、投稿日時を更新
        if upload_flag:
            # データベースに接続し、最終更新日を更新
            await db.connect()
            await db.update_row(
                table_name=table_name,
                row_values={
                    'created_at':update_at
                },
                where_clause={
                    'uuid':webhook.get('uuid')
                }
            )
            table_fetch = await db.select_rows(
                table_name=table_name,
                columns=[],
                where_clause={}
            )

            await db.disconnect()

            # pickleファイルに書き込み
            await pickle_write(
                filename=table_name,
                table_fetch=table_fetch
            )
                        

async def youtube_subsc(
    webhook:Dict,
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
    channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={webhook.get('subscription_id')}&key={youtube_api_key}"
    new_videos_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={webhook.get('subscription_id')}&order=date&type=video&key={youtube_api_key}&maxResults=5"

    # 最終更新日を格納
    created_at = webhook.get('created_at')
    last_upload_time = datetime.strptime(
        created_at, 
        '%a %b %d %H:%M:%S %z %Y'
    )

    async with aiohttp.ClientSession() as sessions:
        async with sessions.get(
            url=new_videos_url
        ) as resp:
            new_videos_info:dict = await resp.json()
            # 最新動画を取得
            videos_item:list[Dict] = new_videos_info.get('items')

        for item in videos_item:
            # 
            upload_time_str = item.get('snippet').get('publishTime')
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
                        channel_info:dict = await re.json()
                        # チャンネルの基本情報を取得
                        channel_item:dict = channel_info.get('items')[0]
                        # チャンネルのアイコンを取得
                        channel_icon_url:str = channel_item.get('snippet').get('thumbnails').get('high').get('url')
                        # チャンネル名を取得
                        channel_title = channel_item.get('snippet').get('title')

                # YouTube動画のタイトル
                video_title = item.get('snippet').get('title')
                # YouTube動画のURL
                video_url = f"https://youtu.be/{item.get('id').get('videoId')}"

                if len(webhook.get('mention_roles')) > 0:
                    # メンションするロールの取り出し
                    mentions = [
                        f"<@&{int(role_id)}> " 
                        for role_id in webhook.get('mention_roles')
                    ]
                    text = " ".join(mentions) + " "

                if len(webhook.get('mention_members')) > 0:
                    members = [
                        f"<@{int(member_id)}> " 
                        for member_id in webhook.get('mention_members')
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
                    if item == videos_item[-1]:
                        # データベースに接続し、最終更新日を更新
                        await db.connect()
                        await db.update_row(
                            table_name=table_name,
                            row_values={
                                'created_at':upload_time.strftime('%a %b %d %H:%M:%S %z %Y')
                            },
                            where_clause={
                                'uuid':webhook.get('uuid')
                            }
                        )

                        table_fetch = await db.select_rows(
                            table_name=table_name,
                            columns=[],
                            where_clause={}
                        )

                        await db.disconnect()

                        # pickleファイルに書き込み
                        await pickle_write(
                            filename=table_name,
                            table_fetch=table_fetch
                        )





async def date_change():
    await db.connect()

    await db.update_row(
        table_name='webhook_854350169055297576.pickle',
        row_values={
            'created_at':''
        },
        where_clause={
            'uuid':''
        }
    )
    table_fetch = await db.select_rows(
        table_name='webhook_854350169055297576.pickle',
        columns=[],
        where_clause={}
    )

    await db.disconnect()

    # pickleファイルに書き込み
    await pickle_write(
        filename='webhook_854350169055297576.pickle',
        table_fetch=table_fetch
    )
    # 読み取り
    webhook_fetch = await pickle_read(filename='webhook_854350169055297576.pickle')

def setup(bot:DBot):
    return bot.add_cog(Webhook_Post(bot))