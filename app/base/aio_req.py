import aiohttp

from discord.channel import (
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
)
from discord import Guild
from discord import ChannelType

from typing import List,Dict,Optional,Tuple,Union

from itertools import groupby,chain
from cryptography.fernet import Fernet

from model_types.discord_type.guild_permission import Permission
from model_types.discord_type.discord_type import DiscordUser

from model_types.environ_conf import EnvConf

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
LINE_BASE_URL = EnvConf.LINE_BASE_URL
DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN
ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

GuildChannel = Union[
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
]

# getリクエストを行う
async def aio_get_request(url: str, headers: dict) -> Dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url = url,
            headers = headers
        ) as resp:
            return await resp.json()

# postリクエストを行う
async def aio_post_request(url: str, headers: dict, data: dict) -> Dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url = url,
            headers = headers,
            data = data
        ) as resp:
            return await resp.json()


async def return_permission(
    user_id:int,
    guild:Guild
) -> Permission:
    """
    指定されたユーザの権限を返す(ロールの権限も含む)

    guild_id        :int
        サーバのid
    user_id         :int
        ユーザのid
    access_token    :str
        ユーザのアクセストークン
    """
    user_permission = Permission()
    role_permission = Permission()
    permission_code = 0
    user = [
        member
        for member in guild.members
        if member.id == user_id
    ]

    # 権限コードをor計算で足し合わせる
    for role in user[0].roles:
        permission_code |= role.permissions.value

    await user_permission.get_permissions(permissions=user[0].guild_permissions.value)
    await role_permission.get_permissions(permissions=permission_code)

    return user_permission | role_permission

async def discord_oauth_check(
    access_token:str
) -> bool:
    """
    OAuth2のトークンが有効か判断する

    param:
    access_token:str
        OAuth2のトークン

    return:
    bool
        トークンが有効な場合、True
        無効の場合、Falseが返される
    """
    oauth_data:dict = await aio_get_request(
        url=f'{DISCORD_BASE_URL}/users/@me',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )
    if oauth_data.get('message') == '401: Unauthorized':
        return False
    else:
        return True

async def line_oauth_check(
    access_token:str
) -> bool:
    """
    OAuth2のトークンが有効か判断する

    param:
    access_token:str
        OAuth2のトークン

    return:
    bool
        トークンが有効な場合、True
        無効の場合、Falseが返される
    """
    oauth_data:dict = await aio_get_request(
        url=f'{LINE_BASE_URL}/oauth2/v2.1/verify?access_token={access_token}',
        headers={}
    )
    if oauth_data.get('error_description') == 'access token expired':
        return False
    else:
        return True

async def get_profile(
    access_token:str
) -> Optional[DiscordUser]:
    """
    OAuth2のトークンが有効か判断する

    param:
    access_token:str
        OAuth2のトークン

    return:
    bool
        トークンが有効な場合、True
        無効の場合、Falseが返される
    """
    oauth_data:dict = await aio_get_request(
        url=f'{DISCORD_BASE_URL}/users/@me',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )
    if oauth_data.get('message') == '401: Unauthorized':
        return None
    else:
        user = DiscordUser(**oauth_data)
        return user

async def sort_discord_channel(
    all_channel:List
) -> List:
    # 親カテゴリー格納用
    position = []

    # レスポンスのJSONからpositionでソートされたリストを作成
    sorted_channels = sorted(all_channel, key=lambda c: c['position'])

    # parent_idごとにチャンネルをまとめた辞書を作成
    channel_dict = {}

    for parent_id, group in groupby(
        sorted_channels,
        key=lambda c: c['parent_id']
    ):
        if parent_id is None:
            # 親カテゴリーのないチャンネルは、キーがNoneの辞書に追加される
            parent_id = 'None'

        # キーがまだない場合、作成(同時に値も代入)
        if channel_dict.get(str(parent_id)) == None:
            channel_dict[str(parent_id)] = list(group)
        # キーがある場合、リストを取り出して結合し代入
        else:
            listtmp:List = channel_dict[str(parent_id)]
            listtmp.extend(list(group))
            channel_dict[str(parent_id)] = listtmp
            # リストを空にする
            listtmp = list()

    # 親カテゴリーがある場合、Noneから取り出す
    for chan in channel_dict['None'][:]:
        if chan['type'] == 4:
            position.append(chan)
            channel_dict['None'].remove(chan)

    # 辞書を表示
    position_index = 0

    # 親カテゴリーの名前をリスト化
    extracted_list = [d["name"] for d in position]
    # カテゴリーに属しないチャンネルが存在する場合
    if len(channel_dict['None']) != 0:
        # 配列の長さをカテゴリー数+1にする
        all_channels = [{}] * (len(extracted_list) + 1)
    else:
        all_channels = [{}] * len(extracted_list)

    for parent_id, channel in channel_dict.items():
        # カテゴリー内にチャンネルがある場合
        if len(channel) != 0:
            for d in position:
                # カテゴリーを探索、あった場合positionを代入
                if d['id'] == channel[0]['parent_id']:
                    position_index = d['position']
                    break
        else:
            position_index = len(extracted_list)

        if len(channel) != 0:
            # 指定したリストの中身が空でない場合、空のリストを探す
            while len(all_channels[position_index]) != 0:
                if len(extracted_list) == position_index:
                    position_index -= 1
                else:
                    position_index += 1

            # 指定した位置にカテゴリー内のチャンネルを代入
            all_channels[position_index] = channel

            # 先頭がカテゴリーでない場合
            if channel[0]['parent_id'] != None:
                # 先頭にカテゴリーチャンネルを代入
                all_channels[position_index].insert(0,d)

    # list(list),[[],[]]を一つのリストにする
    all_channel_sort = list(chain.from_iterable(all_channels))

    return all_channel_sort

async def sort_channels(
    channels:List[GuildChannel]
) -> Tuple[
    Dict[str,List[GuildChannel]],
    Dict[str,GuildChannel]
]:
    """
    Discordのサーバ内のチャンネルをカテゴリーごとにソートする

    Args:
        channels (List[GuildChannel]):
        Discordのチャンネル一覧

    Returns:
        Tuple[ Dict[str,List[GuildChannel]], Dict[str,GuildChannel] ]:
        それぞれ
        カテゴリーごとにソートされたチャンネル一覧
        カテゴリー一覧
    """
    # カテゴリーチャンネルを抽出
    categorys = [
        chan
        for chan in channels
        if chan.type == ChannelType.category
    ]

    # 配列の長さをカテゴリー数+1にする(要素を入れるとappendをする際にすべてのlistに入ってしまう)
    category_list = [[] for _ in range((len(categorys) + 1))]

    category_index = dict()
    category_dict = dict()

    # カテゴリーソート
    categorys = sorted(categorys,key=lambda c:c.position)

    for i,category in enumerate(categorys):
        for chan in channels:
            # カテゴリーチャンネルがある場合
            if chan.category_id == category.id:
                category_list[i].append(chan)
            # カテゴリー所属がない場合、末尾に入れる
            elif (chan.category_id == None and
                chan not in category_list[-1] and
                chan.type != ChannelType.category):
                category_list[-1].append(chan)

        # カテゴリー内のチャンネルごとにソート
        category_list[i] = sorted(category_list[i],key=lambda cc:cc.position)
        category_dict.update({
            str(category.id) : category_list[i]
        })

        category_index.update({
            str(category.id) : category
        })

    category_dict.update({
        'None' : category_list[-1]
    })

    return category_dict,category_index

# 復号化関数
async def decrypt_password(encrypted_password:bytes) -> str:
    """
    byte列の文字の復号化

    Args:
        encrypted_password (bytes): 復号化する文字列

    Returns:
        str: 復号化した文字
    """
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        decrypted_password = cipher_suite.decrypt(encrypted_password)
        return decrypted_password.decode('utf-8')
    # トークンが無効の場合
    except:
        return ''

# 暗号化関数
async def encrypt_password(password:str) -> bytes:
    """
    文字の暗号化

    Args:
        password (str): 暗号化する文字列

    Returns:
        bytes: 暗号化した文字列
    """
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        encrypted_password = cipher_suite.encrypt(password.encode('utf-8'))
        return encrypted_password
    except:
        return b''