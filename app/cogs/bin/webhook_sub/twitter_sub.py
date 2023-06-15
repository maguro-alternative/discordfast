import aiohttp

try:
    from app.cogs.bin.tweetget import Twitter_Get_Tweet
    from app.cogs.bin.base_type.tweet_type import TwitterTweet
except ModuleNotFoundError:
    from cogs.bin.tweetget import Twitter_Get_Tweet
    from cogs.bin.base_type.tweet_type import TwitterTweet

from dotenv import load_dotenv
load_dotenv()

import os
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

    #print(tweetlist)
    
    async with aiohttp.ClientSession() as sessions:
        # 取得したツイートを一つ一つwebhookで送信
        for tweet in tweetlist:
            # 最初の要素の場合
            if tweet == tweetlist[0]:
                # アイコンurl,ユーザ名を取得
                image_url, username = await twitter.get_image_and_name()
            data = {
                'content':tweet
            }
            if username != None:
                data.update({'username':username})
            if image_url != None:
                data.update({'avatar_url':image_url})
            
            async with sessions.post(
                url=webhook_url,
                data=data
            ) as re:
                r = await re.json()
                #print(r)
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