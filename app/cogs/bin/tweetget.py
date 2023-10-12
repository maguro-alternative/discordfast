from pkg.aio_req import (
    aio_get_request
)

from cogs.bin.base_type.tweet_type import TwitterTweet

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime,timezone

from typing import List,Dict,Tuple,Any,Union

from model_types.table_type import WebhookSet

TWEET_GET_BASE_URL = "https://api.twitter.com/1.1/search/tweets.json?q=from%3A"
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

class Twitter_Get_Tweet:
    def __init__(
        self,
        screen_name:str,
        search_word:str
    ) -> None:
        """
        Twitterのツイート取得のクラス
        param:
        screen_name:str
            取得するTwitterのユーザ名(@から始まるid)
        search_word:str
            ツイートの絞り込みをするワード
        """
        self.screen_name = screen_name
        self.search_word = search_word

    async def get_tweet(
        self,
        count:int = 5
    ) -> List[TwitterTweet]:
        """
        ツイートをOAuth1で取得する
        param:
        count:int
            取得するツイートの数
            デフォルトで5

        return:
        List[TwitterTweet]
            ツイート
        """
        url = f"{TWEET_GET_BASE_URL}{self.screen_name}%20{self.search_word}&count={count}"
        headers = {
            'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'
        }
        tweet = await aio_get_request(
            url=url,
            headers=headers
        )

        tweet_statuses:List = tweet.get('stauses')

        # ツイートが取得できなかった場合、空の配列を渡して終了
        if tweet_statuses == None:
            return list()

        twitter_tweet = [
            TwitterTweet(**t)
            for t in tweet_statuses
        ]

        return twitter_tweet

    async def get_image_and_name(self) -> Tuple[str,str]:
        """
        アイコンのurlとユーザ名を取得する

        return:
        Tuple[str,str]
            順にアイコンurl,ユーザ名
        """
        image_url = f"https://api.twitter.com/2/users/by/username/{self.screen_name}?user.fields=profile_image_url"
        headers = {
            'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'
        }
        data = await aio_get_request(
            url=image_url,
            headers=headers
        )
        account:dict = data.get("data")

        if account != None:
            profile_image_url = account.get("profile_image_url")
            account_name= account.get("name")
            if type(profile_image_url) is str:
                profile_image_url = profile_image_url.replace("normal","400x400")
        else:
            profile_image_url = None
            account_name = None

        return profile_image_url, account_name

    async def mention_tweet_make(
        self,
        webhook_fetch:WebhookSet
    ) -> Tuple[List[str],str]:
        """
        ツイートの文章を解析し、メンションするツイートか判断する
        param:
        webhook_fetch:Dict[str,Any]
            webhookテーブルの行、そのまま持ってくる

        return:
        Tuple[List[str],str]
            最新ツイートの配列,最終更新日
        """
        tweet = await self.get_tweet()
        tweetlist = list()
        lastUpdateStr = webhook_fetch.created_at
        for i,tweets in enumerate(tweet):
            # 最新ツイート投稿時刻
            lastUpdate = datetime.strptime(
                tweets.create_at,
                '%a %b %d %H:%M:%S %z %Y'
            )
            # Webhookに最後にアップロードした時刻
            strTime = datetime.strptime(
                webhook_fetch.created_at,
                '%a %b %d %H:%M:%S %z %Y'
            )

            # はじめの要素が最新のツイートなのでその時刻を取得
            if i == 0:
                lastUpdateStr = tweets.create_at

            if strTime < lastUpdate:
                tweet_url = f'https://twitter.com/{self.screen_name}/status/{tweets.id}'
                upload_flag = False
                mention_flag = False


                # ORでNGワード検索
                for word in webhook_fetch.ng_or_word:
                    # NGワードに登録されている場合、False
                    if word in tweets.text:
                        upload_flag = False

                # ANDでNGワードを検索
                for word in webhook_fetch.ng_and_word:
                    # NGワードに登録されている場合、Falseを返し続ける
                    if word in tweets.text:
                        upload_flag = False
                    # NGに一つでも該当しない場合、True
                    else:
                        upload_flag = True
                        break

                # ANDでキーワードを検索
                for word in webhook_fetch.search_and_word:
                    # 条件にそぐわない場合終了
                    if word not in tweets.text:
                        upload_flag = False

                # ORでキーワード検索
                for word in webhook_fetch.search_or_word:
                    if word in tweets.text:
                        upload_flag = True

                # 検索条件がなかった場合、すべて送信
                if (len(webhook_fetch.search_or_word) == 0 and
                    len(webhook_fetch.search_and_word) == 0):
                    upload_flag = True

                # ORでメンションするかどうか判断
                for word in webhook_fetch.mention_or_word:
                    if word in tweets.text:
                        mention_flag = True
                        upload_flag = True

                # ANDでメンションするかどうか判断
                for word in webhook_fetch.mention_and_word:
                    if word not in tweets.text:
                        mention_flag = False
                        upload_flag = True

                text = ""
                if upload_flag:
                    if mention_flag:
                        # メンションするロールの取り出し
                        mentions = [
                            f"<@&{int(role_id)}> "
                            for role_id in webhook_fetch.mention_roles
                        ]
                        members = [
                            f"<@{int(member_id)}> "
                            for member_id in webhook_fetch.mention_members
                        ]
                        text = " ".join(mentions) + " " + " ".join(members) + "\n"

                    text += f'{tweets.text}\n{tweet_url}'

                    tweetlist.append(text)

        return tweetlist,lastUpdateStr