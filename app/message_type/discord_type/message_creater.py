import os
import requests

import aiohttp
import requests
import asyncio
import time

from dotenv import load_dotenv
load_dotenv()

from functools import partial

import asyncio

# DiscordAPIを直接叩いてLINEのメッセージを変換
"""
mes:str
    テキストメッセージ
guild_id
    DiscordのサーバーID
temple_id
    送信する規定のテキストチャンネルのID
profile
    LINEのprofileデータ
"""


"""
ベンチマーク

member_find,role_find,channel_findを並列実行。
変換したテキストをDiscordに送信。

サーバーメンバー            6
ロール数                   8
チャンネル数
    カテゴリーチャンネル    2
    テキストチャンネル      4
    ボイスチャンネル        4
    計                    10

aiohttp使用
    0.8482秒
    1.1233秒
    0.7441秒
    0.7937秒
    0.9899秒

asyncio.loop使用
    1.0416秒
    1.2084秒
    0.9673秒
    0.9959秒
    1.1202秒

同期(loop未使用)
    1.9019秒
    1.6649秒
    1.6858秒
    1.9105秒
    1.9550秒

asyncio.loop使用
res = await self.loop.run_in_executor(
            None,
            partial(
                requests.get,
                f'https://discordapp.com/api/guilds/{self.guild_id}/members?limit={self.limit}',
                headers=self.headers
            )
        )

同期(loop未使用)
res = requests.get(f'https://discordapp.com/api/guilds/{self.guild_id}/members?limit={self.limit}',headers=self.headers)
"""

class ReqestDiscord:
    def __init__(self, guild_id: int, limit: int, token: str) -> None:
        self.guild_id = guild_id
        self.limit = limit
        self.headers = {
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

    async def member_find(self, message: str):
        """
        テキストメッセージのメンションを変換する。
        @ユーザ名#member → @ユーザ名

        戻り値
        @ユーザ名#member 変更前の文字列: str
        <@ユーザid>      変更後の文字列: str 変更がない場合: None
        """
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = f'https://discordapp.com/api/guilds/{self.guild_id}/members?limit={self.limit}',
                headers = self.headers
            ) as resp:
                # 取得したユーザー情報を展開
                res = await resp.json()
                for rs in res:
                    # メッセージに「@{ユーザー名}#member」が含まれていた場合
                    if message.find(f'@{rs["user"]["username"]}#member') >= 0:
                        return f'@{rs["user"]["username"]}#member', f'<@{rs["user"]["id"]}>'
        

    async def role_find(self, message: str):
        """
        テキストメッセージのロールを変換する。
        @ロール名#role → @ロール名

        戻り値
        @ロール名#role   変更前の文字列: str
        <@ロールid>      変更後の文字列: str 変更がない場合: None
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = f'https://discordapp.com/api/guilds/{self.guild_id}/roles',
                headers = self.headers
            ) as resp:
                # 取得したロール情報を取得
                res = await resp.json()
                for rs in res:
                    # メッセージに「@{ロール名}#role」が含まれていた場合
                    if message.find(f'@{rs["name"]}#role') >= 0:
                        return f'@{rs["name"]}#role', f'<@&{rs["id"]}>'
        

    async def channel_find(self, message: str):
        """
        テキストメッセージから送信場所を読み取り変更する。
        テキストチャンネルのみ可能。
        @チャンネル名#channel → 削除

        戻り値
        @チャンネル名#channel 指定したチャンネル名: str
        チャンネルid          指定したチャンネルid: int 変更がない場合: None
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = f'https://discordapp.com/api/guilds/{self.guild_id}/channels',
                headers = self.headers
            ) as resp:
                # 取得したチャンネルを展開
                res = await resp.json()
                for rs in res:
                    # チャンネルのタイプが0(テキストチャンネル)の場合
                    if rs['type'] == 0:
                        # テキストの先頭が「/{チャンネル名}#channel」の場合
                        if message.find(f'/{rs["name"]}#channel') == 0:
                            return f'/{rs["name"]}#channel', int(rs["id"])


class MessageFind(ReqestDiscord):
    """
    Discordへメッセージを送信するクラス

    guild_id    :int
        Discordのサーバーid
    limit       :int
        1度のcallで呼び出す情報の上限
    token       :str
        DiscordBotのトークン
    """
    def __init__(self, guild_id: int, limit: int, token: str) -> None:
        super().__init__(guild_id, limit, token)

    async def send_discord(self, channel_id: int, message: str):
        """
        Discordへメッセージを送信する。

        channel_id  :int
            Discordのテキストチャンネルのid
        message     :str
            テキストメッセージ
        """
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url = f'https://discordapp.com/api/channels/{channel_id}/messages',
                headers = self.headers,data = {'content': f'{message}'}
            ) as resp:
                return await resp.json()


if __name__=="__main__":
    loop = asyncio.get_event_loop()
    r = MessageFind(int(os.environ['6_GUILD_ID']),100,os.environ['TOKEN'])

    message = "/test#channel @マグロ・オルタ#member"
    channel_id = int(os.environ['6_CHANNEL_ID'])

    start = time.time()

    discord_request = loop.run_until_complete(
        asyncio.gather(
            r.member_find(message),
            r.role_find(message),
            r.channel_find(message)
        )
    )

    for req_find in discord_request:
        if req_find != None:
            if type(req_find[1]) is int:
                message = message.lstrip(req_find[0])
                channel_id = req_find[1]
            else:
                message = message.replace(req_find[0], req_find[1])

    loop.run_until_complete(r.send_discord(channel_id=channel_id, message=message))

    end = time.time() - start

    print(message)
    print(end)
