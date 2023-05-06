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
from datetime import datetime

from base.database import PostgresDB

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
            async with aiofiles.open(
                file=f'{table_name}.pickle',
                mode='rb'
            ) as f:
                pickled_bytes = await f.read()
                with io.BytesIO() as f:
                    f.write(pickled_bytes)
                    f.seek(0)
                    webhook_fetch = pickle.load(f)

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
                            # クラスを宣言
                            twitter = Twitter_Get_Tweet(
                                screen_name=webhook.get('subscription_id'),
                                search_word=""
                            )
                            # アイコンurl,ユーザ名を取得
                            image_url, username = await twitter.get_image_and_name()
                            # 最新ツイートと更新日時を取得(ない場合はそのまま)
                            tweetlist, create_at = await twitter.mention_tweet_make(
                                webhook_fetch=webhook
                            )
                            
                            async with aiohttp.ClientSession() as sessions:
                                # 取得したツイートを一つ一つwebhookで送信
                                for tweet in tweetlist:
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

                                            # 取り出して書き込み
                                            dict_row = [
                                                dict(zip(record.keys(), record)) 
                                                for record in table_fetch
                                            ]

                                            # 書き込み
                                            async with aiofiles.open(
                                                file=f'{table_name}.pickle',
                                                mode='wb'
                                            ) as f:
                                                await f.write(pickle.dumps(obj=dict_row))

                                            return await re.json()

                        # niconicoの場合
                        if webhook.get('subscription_type') == 'niconico':
                            # rssのurl
                            niconico_rss_url = f"https://www.nicovideo.jp/user/{webhook.get('subscription_id')}/video?rss=2.0"
                            # rssを取得し展開
                            niconico = feedparser.parse(
                                url_file_stream_or_string=niconico_rss_url
                            )
                            
                            # 最終更新日を格納
                            create_at = webhook.get('created_at')

                            async with aiohttp.ClientSession() as sessions:
                                # 最新の動画を一つ一つ処理
                                for entry in niconico.entries:
                                    # Webhookに最後にアップロードした時刻
                                    strTime = datetime.strptime(
                                        webhook.get('created_at'), 
                                        '%a %b %d %H:%M:%S %z %Y'
                                    )
                                    # 動画の投稿時刻
                                    lastUpdate = datetime.strptime(
                                        entry.published,
                                        '%a, %d %b %Y %H:%M:%S %z'
                                    )
                                    # 最初の要素の場合(最新の要素)
                                    if entry == niconico.entries[0]:
                                        create_at = entry.published
                                    
                                    # htmlとしてパース
                                    soup = BeautifulSoup(entry.summary, 'html.parser')
                                    
                                    # 最新の動画が投稿されていた場合
                                    if strTime < lastUpdate:
                                        # すべてのimgタグのsrcを取得する
                                        img_src_list = [
                                            img['src'] 
                                            for img in soup.find_all('img')
                                        ]

                                        upload_flag = True
                                        mention_flag = True

                                        text = ""
                                        if upload_flag:
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
                                        
                                            async with sessions.post(
                                                url=webhook_url,
                                                data={
                                                    'username':'ニコニコ新作',
                                                    'avatar_url':img_src_list[0],
                                                    'content':text
                                                }
                                            ) as re:
                                                # 最後の要素の場合
                                                if entry == niconico.entries[-1]:
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

                                                    # 取り出して書き込み
                                                    dict_row = [
                                                        dict(zip(record.keys(), record)) 
                                                        for record in table_fetch
                                                    ]

                                                    # 書き込み
                                                    async with aiofiles.open(
                                                        file=f'{table_name}.pickle',
                                                        mode='wb'
                                                    ) as f:
                                                        await f.write(pickle.dumps(obj=dict_row))

                                                    return await re.json()


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

    # 取り出して書き込み
    dict_row = [
        dict(zip(record.keys(), record)) 
        for record in table_fetch
    ]

    # 書き込み
    async with aiofiles.open(
        file='webhook_854350169055297576.pickle',
        mode='wb'
    ) as f:
        await f.write(pickle.dumps(obj=dict_row))
    # 読み取り
    async with aiofiles.open(
        file=f'webhook_854350169055297576.pickle',
        mode='rb'
    ) as f:
        pickled_bytes = await f.read()
        with io.BytesIO() as f:
            f.write(pickled_bytes)
            f.seek(0)
            webhook_fetch = pickle.load(f)

def setup(bot:DBot):
    return bot.add_cog(Webhook_Post(bot))