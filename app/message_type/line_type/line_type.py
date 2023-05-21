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

# 
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

if __name__ == "__main__":
    import os
    
    from dotenv import load_dotenv
    load_dotenv()

    import requests
    import asyncio

    loop = asyncio.get_event_loop()

    line_group_id = os.environ.get('FIVE_GROUP_ID')
    line_bot_token = os.environ.get('FIVE_BOT_TOKEN')
    user_id = os.environ.get('FIVE_USER_ID')
    group_url = f"https://api.line.me/v2/bot/group/{line_group_id}/member/{user_id}"
    profile_url = f"https://api.line.me/v2/bot/profile/{user_id}"

    gro = requests.get(
        url=profile_url,
        headers = {'Authorization': 'Bearer ' + line_bot_token}
    ).json()
    print(gro)

    l = loop.run_until_complete(Profile.new_from_json_dict(data=gro))
    print(l.display_name)
    