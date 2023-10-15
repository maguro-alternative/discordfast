import aiohttp

try:
    from app.cogs.bin.tweetget import Twitter_Get_Tweet
    from app.cogs.bin.base_type.tweet_type import TwitterTweet
    from app.core.db_create import DB
    from app.model_types.table_type import WebhookSet
except ModuleNotFoundError:
    from cogs.bin.tweetget import Twitter_Get_Tweet
    from cogs.bin.base_type.tweet_type import TwitterTweet
    from core.db_create import DB
    from model_types.table_type import WebhookSet

from dotenv import load_dotenv
load_dotenv()

async def twitter_subsc(
    webhook:WebhookSet,
    webhook_url:str,
    table_name:str
) -> None:
    """
    twitterの最新ツイートを取得し、WebHookで投稿する

    pream:
    webhook:WebhookSet
        webhookの情報を示す辞書型オブジェクト
    webhook_url
        webhookのurl
    table_name
        webhookの情報が登録されているテーブル名
    """
    # クラスを宣言
    twitter = Twitter_Get_Tweet(
        screen_name=webhook.subscription_id,
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
                    if DB.conn == None:
                        await DB.connect()

                    await DB.update_row(
                        table_name=table_name,
                        row_values={
                            'created_at':create_at
                        },
                        where_clause={
                            'uuid':webhook.uuid
                        }
                    )