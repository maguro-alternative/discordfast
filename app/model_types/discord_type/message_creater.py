import re
import io

import aiohttp

from typing import List,Tuple,Dict

from model_types.discord_type.discord_type import (
    DiscordMember,
    DiscordRole,
    DiscordChannel
)

from model_types.file_type import AudioFiles

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

DISCORD_BASE_URL = "https://discord.com/api"

class ReqestDiscord:
    def __init__(self, guild_id: int, limit: int, token: str) -> None:
        """
        DiscordAPIのクラス

        param:
        guild_id    :int
        サーバーid

        limit       :int
        一度に取得するパラメータの数

        token       :str
        DiscordBotのトークン
        """
        self.guild_id = guild_id
        self.limit = limit
        self.headers = {
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        # ファイルアップロードの際にContent-Typeが邪魔になるので取り除く
        self.no_content_headers = {
            'Authorization': f'Bot {token}'
        }

    async def member_get(self) -> List[DiscordMember]:
        """
        サーバーのユーザーを取得する。
        戻り値
        List[DiscordMember]
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f'{DISCORD_BASE_URL}/guilds/{self.guild_id}/members?limit={self.limit}',
                headers=self.headers
            ) as resp:
                # 取得したユーザー情報を展開
                res:Dict = await resp.json()
                member_list = []
                for member in res:
                    r = DiscordMember(**member)
                    member_list.append(r)

        return member_list


    async def role_get(self) -> List[DiscordRole]:
        """
        ロールを取得する。
        戻り値
        List[DiscordRole]
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f'{DISCORD_BASE_URL}/guilds/{self.guild_id}/roles',
                headers=self.headers
            ) as resp:
                # 取得したロール情報を取得
                res = await resp.json()
                role_list = []
                for role in res:
                    r = DiscordRole(**role)
                    role_list.append(r)

        return role_list

    async def channel_get(self) -> List[DiscordChannel]:
        """
        チャンネルを取得する。
        戻り値
        List[DiscordChannel]
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f'{DISCORD_BASE_URL}/guilds/{self.guild_id}/channels',
                headers=self.headers
            ) as resp:
                # 取得したチャンネルを展開
                res = await resp.json()
                channel_list = []
                for channel in res:
                    r = DiscordChannel(**channel)
                    channel_list.append(r)

        return channel_list

    async def channel_info_get(self,channel_id:int) -> DiscordChannel:
        """
        チャンネル情報を取得する。

        param:
        channel_id:int
        チャンネルid

        戻り値
        Discord_Channel
        """

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f'{DISCORD_BASE_URL}/channels/{channel_id}',
                headers=self.headers
            ) as resp:
                # 取得したチャンネルを展開
                res = await resp.json()

                r = DiscordChannel(**res)
        return r

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
                message = message.replace(
                    f'@{member.user.username}#{member.user.discreminator}#member',
                    f'<@{member.user.id}>'
                )
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

    async def send_discord(self, channel_id: int, message: str) -> Dict:
        """
        Discordへメッセージを送信する。

        channel_id  :int
            Discordのテキストチャンネルのid
        message     :str
            テキストメッセージ
        """

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f'{DISCORD_BASE_URL}/channels/{channel_id}/messages',
                headers=self.headers,
                data={'content': f'{message}'}
            ) as resp:
                return await resp.json()


    async def send_discord_file(
        self,
        channel_id: int,
        message: str,
        fileobj:AudioFiles,
        content_type:str=None
    ) -> Dict:
        """
        Discordへファイル付きのメッセージを送信する。

        channel_id  :int
            Discordのテキストチャンネルのid
        message     :str
            テキストメッセージ
        fileobj     :AudioFiles
            音声ファイルのオブジェクト
        """

        with aiohttp.MultipartWriter("form-data") as mpwriter:
            # ファイルを送付
            mpwriter.append(
                obj=io.BytesIO(fileobj.byte)
            ).set_content_disposition(
                disptype='form-data',
                name=fileobj.filename,
                filename=fileobj.filename
            )

            # テキストメッセージを送付
            mpwriter.append(
                obj=message
            ).set_content_disposition(
                disptype='form-data',
                name="content"
            )

            # content_typeが指定されている場合、更新
            content_headers = self.no_content_headers
            if content_type:
                content_headers.update(
                    {
                        'content_type': content_type
                    }
                )

            # Discordにファイルとメッセージを送信
            # 'Content-Type': 'application/x-www-form-urlencoded'が邪魔なので取り除く
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url = f'{DISCORD_BASE_URL}/channels/{channel_id}/messages',
                    headers = content_headers,
                    data = mpwriter
                ) as resp:
                    return await resp.json()

