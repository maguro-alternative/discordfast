import os
import re

import aiohttp
import requests
import asyncio
import time

from dotenv import load_dotenv
load_dotenv()

from functools import partial
from typing import List,Tuple

import asyncio

#from discord_type import Discord_Member,Discord_Role,Discord_Channel
from message_type.discord_type.discord_type import Discord_Member,Discord_Role,Discord_Channel

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

    async def member_get(self) -> List[Discord_Member]:
        """
        サーバーのユーザーを取得する。
        戻り値
        Discord_Member
        """
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = f'https://discordapp.com/api/guilds/{self.guild_id}/members?limit={self.limit}',
                headers = self.headers
            ) as resp:
                # 取得したユーザー情報を展開
                res = await resp.json()
                member_list = []
                for member in res:
                    r = Discord_Member.new_from_json_dict(member)
                    member_list.append(r)
        
        return member_list
            

    async def role_get(self) -> List[Discord_Role]:
        """
        ロールを取得する。
        戻り値
        Discord_Role
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = f'https://discordapp.com/api/guilds/{self.guild_id}/roles',
                headers = self.headers
            ) as resp:
                # 取得したロール情報を取得
                res = await resp.json()
                role_list = []
                for role in res:
                    r = Discord_Role.new_from_json_dict(role)
                    role_list.append(r)

        return role_list

    async def channel_get(self) -> List[Discord_Channel]:
        """
        チャンネルを取得する。
        戻り値
        Discord_Channel
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url = f'https://discordapp.com/api/guilds/{self.guild_id}/channels',
                headers = self.headers
            ) as resp:
                # 取得したチャンネルを展開
                res = await resp.json()
                channel_list = []
                for channel in res:
                    r = Discord_Channel.new_from_json_dict(channel)
                    channel_list.append(r)

        return channel_list

    async def members_find(self, message: str) -> str:
        """
        テキストメッセージのメンションを変換する。
        @ユーザ名#4桁の数字#member → @ユーザ名

        戻り値
        message      変更後の文字列: str
        """
        
        # @{空白以外の0文字以上}#{0以上の数字}#member
        member_mention_list = re.findall("@\S*?#\d*?#member",message,re.S)

        if not member_mention_list:
            return message
        
        get_member_list = await self.member_get()

        for member in get_member_list:
            # ユーザー名の空白文字を削除
            member.user.username = re.sub("[\u3000 \t]", "",member.user.username)

            # メッセージに「@{ユーザー名}#{4桁の数字}member」が含まれていた場合
            if f'@{member.user.username}#{member.user.discreminator}#member' in member_mention_list:
                message = message.replace(f'@{member.user.username}#{member.user.discreminator}#member',f'<@{member.user.id}>')
                member_mention_list = [
                    user for user in member_mention_list 
                    if user != f'@{member.user.username}#{member.user.discreminator}#member'
                ]
            if not member_mention_list:
                return message

        return message


    async def roles_find(self, message: str) -> str:
        """
        テキストメッセージのメンションを変換する。
        @ロール名#role → @ロール名

        戻り値
        message      変更後の文字列: str
        """
        
        role_list = re.findall("@\S*?#role",message,re.S)

        if not role_list:
            return message
        
        get_role_list = await self.role_get()

        for role in get_role_list:
            # ロール名の空白文字を削除
            role.name = re.sub("[\u3000 \t]", "",role.name)

            # メッセージに「@{ロール名}#role」が含まれていた場合
            if f'@{role.name}#role' in role_list:
                message = message.replace(f'@{role.name}#role',f'<@&{role.id}>')
                role_list = [
                    rolename for rolename in role_list 
                    if rolename != f'@{role.name}#role'
                ]
            if not role_list:
                return message

        return message
                
        
    async def channel_select(self, channel_id: int, message: str) -> Tuple[int,str]:
        """
        テキストメッセージから送信場所を読み取り変更する。
        テキストチャンネルのみ可能。
        /チャンネル名#channel → 削除

        戻り値
        channel_id      送信先のチャンネル      :id
        message         指定したチャンネル名    :str
        """
        
        channel_list = re.findall("\A/\S*?#channel",message,re.S)

        if not channel_list or message.find('/') != 0:
            return channel_id, message
        
        get_channel_list = await self.channel_get()

        for channel in get_channel_list:
            # チャンネル名の空白文字を削除
            channel.name = re.sub("[\u3000 \t]", "",channel.name)

            # メッセージの先頭に「/{チャンネル名}#channel」が含まれていた場合
            if message.find(f'/{channel.name}#channel') == 0 and channel.type == 0:
                message = message.lstrip(f'/{channel.name}#channel')
                channel_id = channel.id
                return channel_id, message

        return channel_id, message

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



if __name__=="_main__":
    loop = asyncio.get_event_loop()
    r = ReqestDiscord(int(os.environ['6_GUILD_ID']),100,os.environ['TOKEN'])

    message = "/test#channel @マグロ・オルタ#member @マグロ#member"
    channel_id = int(os.environ['6_CHANNEL_ID'])

    start = time.time()

    discord_request = loop.run_until_complete(
        asyncio.gather(
            r.members_find(message),
            r.roles_find(message),
            r.channel_select(message)
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

if __name__=="__main__":
    loop = asyncio.get_event_loop()
    res = ReqestDiscord(int(os.environ['PRO_GUILD_ID']),100,os.environ['PRO_TOKEN'])
    r=loop.run_until_complete(
        res.role_get()
        #asyncio.gather(
        #    r.member_get(),
        #    r.role_get(),
        #    r.channel_get()
        #)
    )
    print(r[0].name)
