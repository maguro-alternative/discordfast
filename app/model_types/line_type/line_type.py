import re
import json

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

    async def as_json_string(self):
        """jsonの文字列を返します。 

        :rtype: str
        """
        return json.dumps(self.as_json_dict(), sort_keys=True)

    async def as_json_dict(self):
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
    async def new_from_json_dict(cls, data:dict):
        """dict から新しいインスタンスを作成します。

        :param data: JSONのディクショナリ
        """
        new_data = {await to_snake_case(key): value
                    for key, value in data.items()}

        return cls(**new_data)


async def to_snake_case(text:str):
    """スネークケースに変換する。

    :param str text:
    :rtype: str
    """
    s1 = re.sub('(.)([A-Z])', r'\1_\2', text)
    s2 = re.sub('(.)([0-9]+)', r'\1_\2', s1)
    s3 = re.sub('([0-9])([a-z])', r'\1_\2', s2)
    return s3.lower()

async def to_camel_case(text:str):
    """キャメルケースに変換する。

    :param str text:
    :rtype: str
    """
    split = text.split('_')
    return split[0] + "".join(x.title() for x in split[1:])

class Profile(Base):
    """
    LINE Message APIのProfileクラス

    user_id         :LINEユーザーのid
    display_name    :LINEのユーザー名
    picture_url     :LINEのアイコンurl
    status_message  :LINEのプロフィール文
    """
    def __init__(self,
        user_id:str = None,
        display_name:str = None,
        picture_url:str = None,
        status_message:str = None,
        **kwargs
    ):
        super(Profile, self).__init__(**kwargs)
        self.user_id = user_id
        self.display_name = display_name
        self.picture_url = picture_url
        self.status_message = status_message


class GyazoJson(Base):
    """
    Gyazoの画像クラス

    image_id        :画像id
    permalink_url   :画像のパーマリンク
    thumb_url       :サムネイル画像url
    url             :画像url
    type            :拡張子のタイプ
    """
    def __init__(self,
                image_id:str=None,
                permalink_url:str=None,
                thumb_url:str=None,
                url:str=None,
                type:str=None,
                **kwargs
    ):
        self.image_id = image_id
        self.premalink_url = permalink_url
        self.thumb_url = thumb_url
        self.url = url
        self.type = type
        super(GyazoJson,self).__init__(**kwargs)

from pydantic import BaseModel,validator
from typing import List,Optional,Dict,Union,Any

class LineBotInfo(BaseModel):
    """
    ボットの情報
    https://developers.line.biz/ja/reference/messaging-api/#get-bot-info

    Args:
    basicId             :Optional[str]
        ボットのベーシックID
    chatMode            :Optional[str]
        チャットの設定
        chat:チャットがオン
        bot :チャットがオフ
    markAsReadMode      :Optional[str]
        メッセージの自動既読設定
        auto    :自動既読設定が有効
        manual  :自動既読設定が無効
    premiumId           :Optional[str]
        ボットのプレミアムID
        プレミアムIDが未設定の場合、この値は含まれない
    pictureUrl          :Optional[str]
        プロフィール画像のURL。「https://」から始まる画像UR
        ボットにプロフィール画像を設定していない場合は、レスポンスに含まれない
    userId              :Optional[str]
        ボットのユーザーID
    message             :Optional[str]
        エラー情報を含むメッセージ
    details             :Optional[List[Dict[str,str]]]
        エラー詳細の配列
        配列が空の場合は、レスポンスに含まれない
    """
    basicId             :Optional[str]
    chatMode            :Optional[str]
    markAsReadMode      :Optional[str]
    premiumId           :Optional[str]
    pictureUrl          :Optional[str]
    userId              :Optional[str]
    message             :Optional[str]
    details             :Optional[List[Dict[str,str]]]

class LineBotFriend(BaseModel):
    """
    LINE Botの友達数
    https://developers.line.biz/ja/reference/messaging-api/#get-number-of-followers

    Args:
    status          :Optional[str]
        集計処理の状態
        ready:数値を取得
        unready:dateに指定した日付の友だち数の集計がまだ完了してない
        out_of_service:dateに指定した日付が、集計システムの稼働開始日（2016年11月1日）より前
    followers       :Optional[int]
        dateに指定した日付までに、アカウントが友だち追加された回数
    targetedReaches :Optional[int]
        dateに指定した日付時点の、性別や年齢、地域で絞り込んだターゲティングメッセージの配信先となりうる友だちの総数
    blocks          :Optional[int]
        dateに指定した日付時点で、アカウントをブロックしているユーザーの数
    message         :Optional[str]
        エラーメッセージ
    """
    status          :Optional[str]
    followers       :Optional[int]
    targetedReaches :Optional[int]
    blocks          :Optional[int]
    message         :Optional[str]

class LineGroupCount(BaseModel):
    """
    LINEグループにいる人数
    https://developers.line.biz/ja/reference/messaging-api/#get-quota

    Args:
    count   :Optional[int]
        人数
    message :Optional[str]
        エラーメッセージ
    """
    count   :Optional[int]
    message :Optional[str]

class LineBotQuota(BaseModel):
    """
    LINE Botの送信上限
    https://developers.line.biz/ja/reference/messaging-api/#get-quota

    Args:
    type    :Optional[str]
        上限目安が設定されているかどうかを示す値
        none:上限目安が未設定であることを示す
        limited:上限目安が設定されていることを示す
    value   :Optional[int]
        当月に送信できるメッセージ数の上限目安
    message :Optional[str]
        エラーメッセージ
    """
    type    :Optional[str]
    value   :Optional[int]
    message :Optional[str]

class LineBotConsumption(BaseModel):
    """
    LINE Botが送ったメッセージ数
    https://developers.line.biz/ja/reference/messaging-api/#get-consumption

    Args:
    totalUsage  :Optional[int]
        送ったメッセージの総数
    message     :Optional[str]
        エラーメッセージ
    """
    totalUsage  :Optional[int]
    message     :Optional[str]