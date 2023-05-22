from typing import List

import re
import json

def to_snake_case(text:str):
    """スネークケースに変換する。

    :param str text:
    :rtype: str
    """
    s1 = re.sub('(.)([A-Z])', r'\1_\2', text)
    s2 = re.sub('(.)([0-9]+)', r'\1_\2', s1)
    s3 = re.sub('([0-9])([a-z])', r'\1_\2', s2)
    return s3.lower()

def to_camel_case(text:str):
    """キャメルケースに変換する。

    :param str text:
    :rtype: str
    """
    split = text.split('_')
    return split[0] + "".join(x.title() for x in split[1:])

class Base(object):
    def __init__(self, **kwargs):
        """__init__ method.

        :param kwargs:
        """
        pass

    def __str__(self):
        """__str__ method."""
        return self.as_json_string()

    def __repr__(self):
        """__repr__ method."""
        return str(self)

    def __eq__(self, other):
        """__eq__ method.

        :param other:
        """
        return other and self.as_json_dict() == other.as_json_dict()

    def __ne__(self, other):
        """__ne__ method.

        :param other:
        """
        return not self.__eq__(other)

    def as_json_string(self):
        """jsonの文字列を返します。 

        :rtype: str
        """
        return json.dumps(self.as_json_dict(), sort_keys=True, ensure_ascii=False)

    def as_json_dict(self):
        """このオブジェクトから辞書型を返します。

        :return: dict
        """
        data = {}
        for key, value in self.__dict__.items():
            camel_key = to_camel_case(key)
            if isinstance(value, (list, tuple, set)):
                data[camel_key] = list()
                for item in value:
                    if hasattr(item, 'as_json_dict'):
                        data[camel_key].append(item.as_json_dict())
                    else:
                        data[camel_key].append(item)

            elif hasattr(value, 'as_json_dict'):
                data[camel_key] = value.as_json_dict()
            elif value is not None:
                data[camel_key] = value

        return data

    @classmethod
    def new_from_json_dict(cls, data:dict):
        """dict から新しいインスタンスを作成します。

        :param data: JSONのディクショナリ
        """
        new_data = {to_snake_case(key): value
                    for key, value in data.items()}

        return cls(**new_data)

"""
class Discord_Member(Base):
    def __init__(
        self, 
        id:int,
        username:str,
        discriminator:str,
        avatar:str,
        verified:bool,
        email:str,
        flags:int,
        banner:str,
        accent_color:int,
        premium_type:int,
        public_flags:int,
        **kwargs
    ):
        super().__init__(**kwargs)
"""
class User(Base):
    """
    DiscordのUserクラス

    id                  :ユーザーid
    username            :ユーザー名
    avatar              :ユーザーのアバターハッシュ
    avatar_decoration   :ユーザーのアバターのデコレーション
    discriminator       :4桁のユーザー番号
    public_flags        :ユーザーアカウントの公開フラグ
    bot                 :botかどうか
    """
    def __init__(
        self, 
        id:int = None,
        username:str = None,
        avatar:str = None,
        avatar_decoration:str = None,
        discriminator:str = None,
        public_flags:int = None,
        bot:bool = None,
        **kwargs
    ):
        self.id = id
        self.username = username
        self.avater = avatar
        self.avater_decoration = avatar_decoration
        self.discreminator = discriminator
        self.public_flags = public_flags
        self.bot = bot
        super().__init__(**kwargs)

class Permission(Base):
    """
    Discordのチャンネルの権限のクラス
    上書きする際に使用

    id          :チャンネルのid
    type        :チャンネルのタイプ
    allow       :許可されている権限
    deny        :禁止されている権限
    allow_new   :新たなに許可する権限
    deny_new    :新たに禁止する権限
    """
    def __init__(
        self, 
        id:int = None,
        type:str = None,
        allow:int = None,
        deny:int = None,
        allow_new:int = None,
        deny_new:int = None,
        **kwargs
    ):
        self.id = id
        self.type = type
        self.allow = allow
        self.deny = deny
        self.allow_new = allow_new
        self.deny_new = deny_new
        super().__init__(**kwargs)

class Discord_Member(Base):
    """
    Discordのユーザーのサーバーでのステータス

    user        :Discordのユーザークラス
    nick        :ニックネーム
    is_pending  :用途不明   https://github.com/discord/discord-api-docs/issues/2235
    flags       :こちらも用途不明
    avatar      :ユーザーのアバターハッシュ
    roles       :サーバーで割り当てられているロール
    joined_at   :参加した日付
    deaf        :スピーカーミュートしているか
    mute        :マイクミュートしているか
    """
    def __init__(
        self, 
        user:User = None,
        nick:str = None,
        is_pending:bool = None,
        flags:int = None,
        avatar:str = None,
        roles:List[int] = None,
        joined_at:str = None,
        deaf:bool = None,
        mute:bool = None,
        **kwargs
    ):
        self.user = User.new_from_json_dict(user)
        self.nick = nick
        self.is_pending = is_pending
        self.flags = flags
        self.avatar = avatar
        self.roles = roles
        self.joined_at = joined_at
        self.deaf = deaf
        self.mute = mute
        super().__init__(**kwargs)

class Discord_Role(Base):
    """
    id              :ロールid
    name            :ロール名
    description     :ロールの説明
    permissions     :ロールに割り当てられている権限
    position        :ロールの順番
    color           :ロールの色
    hoist           :オンラインメンバーとは別に表示するか
    managed         :管理者権限?
    mentionable     :メンション可能かどうか
    icon            :サーバーにギルドアイコン機能がある場合、その画像
    unicode_emoji   :ギルドアイコン機能での絵文字
    flags           :用途不明
    permissions_new :新たに設定する権限
    """
    def __init__(
        self, 
        id:int = None,
        name:str = None,
        description:str = None,
        permissions:int = None,
        position:int = None,
        color:int = None,
        hoist:bool = None,
        managed:bool = None,
        mentionable:bool = None,
        icon:str = None,
        unicode_emoji:str = None,
        flags:int = None,
        permissions_new:int = None,
        **kwargs
    ):
        self.id = id
        self.name = name
        self.description = description
        self.permissions = permissions
        self.position = position
        self.color = color
        self.hoist = hoist
        self.managed = managed
        self.mentionable = mentionable
        self.icon = icon
        self.unicode_emoji = unicode_emoji
        self.flags = flags
        self.permissions_new = permissions_new
        super().__init__(**kwargs)

class Discord_Channel(Base):
    """
    Discordのチャンネルのクラス

    id                      :チャンネルid
    last_message_id         :最後に発言されたメッセージのid
    type                    :チャンネルのタイプ(0の場合、テキストチャンネル)
    name                    :チャンネル名
    position                :チャンネルの順番
    flags                   :用途不明
    parent_id               :親チャンネルのid
    bitrate                 :音声のビットレート
    user_limit              :ボイスチャンネルのユーザーの上限
    rtc_region              :音声のリージョン
    topic                   :チャンネルのトピックス
    guild_id                :サーバーid
    premission_overwrites   :新たに設定する権限
    rate_limit_per_user     :低速モードで再び発言できるまでの秒数
    nsfw                    :閲覧注意チャンネルかどうか
    """
    def __init__(
        self, 
        id:int = None,
        last_message_id:int = None,
        type:int = None,
        name:str = None,
        position:int = None,
        flags:int = None,
        parent_id:str = None,
        bitrate:int = None,
        user_limit:int = None, 
        rtc_region:str = None,
        topic:str = None,
        guild_id:int = None,
        permission_overwrites:List[Permission] = None,
        rate_limit_per_user:int = None,
        nsfw:bool = None,
        **kwargs
    ):
        self.id = id
        self.last_message_id = last_message_id
        self.type = type
        self.name = name
        self.position = position
        self.flags = flags
        self.parent_id = parent_id
        self.bitrate = bitrate
        self.user_limit = user_limit 
        self.rtc_region = rtc_region
        self.topic = topic
        self.guild_id = guild_id
        self.permission_overwrites = permission_overwrites
        self.rate_limit_per_user = rate_limit_per_user
        self.nsfw = nsfw
        super().__init__(**kwargs)

if __name__ == "__main__":
    import os
    
    from dotenv import load_dotenv
    load_dotenv()

    import requests
    import asyncio

    loop = asyncio.get_event_loop()
