from base.guild_permission import Permission
import aiohttp
import aiofiles

from typing import List,Any,Dict

import os
import io
import pickle

from itertools import groupby,chain
from cryptography.fernet import Fernet

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]

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

async def pickle_read(filename:str) -> Any:
    """
    pickleファイルの読み込み

    param:
    filename:str
        pickleファイルの名前

    return:
        pickleファイルの中身
    """
    # 読み取り
    async with aiofiles.open(
        file=f'{filename}.pickle',
        mode='rb'
    ) as f:
        pickled_bytes = await f.read()
        with io.BytesIO() as f:
            f.write(pickled_bytes)
            f.seek(0)
            fetch = pickle.load(f)
            return fetch

async def pickle_write(
    filename:str,
    table_fetch:List[Dict]
) -> None:
    """
    pickleファイルの書き込み

    param:
    filename    :str
        pickleファイルの名前

    table_fetch :List[Dict]
        SQLから取り出したデータ
    """
    # 取り出して書き込み
    dict_row = [
        dict(zip(record.keys(), record.values())) 
        for record in table_fetch
    ]
    # 書き込み
    async with aiofiles.open(
        file=f'{filename}.pickle',
        mode='wb'
    ) as f:
        await f.write(pickle.dumps(obj=dict_row))


async def search_guild(
    bot_in_guild_get:List[dict],
    user_in_guild_get:List[dict]
) -> List:
    """
    Botとログインしたユーザーが所属しているサーバーを調べ、同じものを返す

    param:
    bot_in_guild_get    :List[dict]
        Botが所属しているサーバー一覧

    user_in_guild_get   :List[dict]
        ユーザーが所属しているサーバー一覧

    return:
    List
        所属が同じサーバー一覧
    """

    bot_guild_id = []
    user_guild_id = []
    match_guild = []

    bot_guild_id = [
        bot_guild.get('id')
        for bot_guild in bot_in_guild_get
    ]

    user_guild_id = [
        user_guild.get('id')
        for user_guild in user_in_guild_get
    ]

    # for探索短縮のため、総数が少ない方をforinする
    if len(bot_guild_id) < len(user_guild_id):
        match_guild = [
            guild
            for guild_id,guild in zip(bot_guild_id,bot_in_guild_get)
            if guild_id in user_guild_id
        ]

    else:
        match_guild = [
            guild
            for guild_id,guild in zip(user_guild_id,user_in_guild_get)
            if guild_id in bot_guild_id
        ]


    return match_guild


async def search_role(
    guild_role_get:List[dict],
    user_role_get:List[dict]
) -> List[dict]:
    """
    ユーザがサーバ内で持っているロールの詳細を取得する

    param:
    guild_role_get  :List[dict]
        サーバにある全てのロール
    user_role_get   :List[dict]
        ユーザ情報

    return:
    List
        ユーザーが持っているロール一覧
    """
    guild_role_id = []
    user_role_id = []
    match_role = []

    for guild_role in guild_role_get:
        guild_role_id.append(guild_role['id'])

    for user_guild in user_role_get["roles"]:
        user_role_id.append(user_guild)

    for role_id,role in zip(guild_role_id,guild_role_get):
        if role_id in user_role_id:
            match_role.append(role)

    return match_role

async def return_permission(
    guild_id:int,
    user_id:int,
    access_token:str
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

    # ログインユーザの情報を取得
    guild_user = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{user_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバのロールを取得
    guild_role = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/roles',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ログインユーザのロールの詳細を取得
    match_role = await search_role(
        guild_role_get = guild_role,
        user_role_get = guild_user
    )

    # ログインユーザの所属しているサーバを取得
    guild_info = await aio_get_request(
        url = DISCORD_BASE_URL + f'/users/@me/guilds',
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
    )

    permission = 0
    user_permission = Permission()

    # サーバでの権限を取得
    for info in guild_info:
        if str(guild_id) == info["id"]:
            permission = info["permissions"]
            break

    await user_permission.get_permissions(permissions=permission)

    for role in match_role:
        # サーバー管理者であるかどうかを調べる
        role_permission = Permission()
        await role_permission.get_permissions(permissions=int(role["permissions"]))
        user_permission = user_permission | role_permission

    return user_permission


async def check_permission(
    guild_id:int,
    user_id:int,
    access_token:str,
    permission_16:int
) -> bool:
    """
    指定されたユーザが権限を持っているか確認

    guild_id        :int
        サーバのid
    user_id         :int
        ユーザのid
    access_token    :str
        ユーザのアクセストークン
    permission_16   :int
        確認する権限、16進数で構成されている
        詳細はdiscordのリファレンスを参照
    """
    # 指定されたパーミッションはあるか
    user_permission:bool = False

    # ログインユーザの情報を取得
    guild_user = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{user_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # サーバのロールを取得
    guild_role = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/roles',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ログインユーザのロールの詳細を取得
    match_role = await search_role(
        guild_role_get = guild_role,
        user_role_get = guild_user
    )

    # ログインユーザの所属しているサーバを取得
    guild_info = await aio_get_request(
        url = DISCORD_BASE_URL + f'/users/@me/guilds',
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
    )

    permission = None

    # サーバでの権限を取得
    for info in guild_info:
        if str(guild_id) == info["id"]:
            permission = info["permissions"]
            break

    if len(match_role) == 0:
        if permission & permission_16 == permission_16:
            user_permission = True

    for role in match_role:
        # サーバー管理者であるかどうかを調べる
        if (permission & permission_16 == permission_16 or
            int(role["permissions"]) & permission_16 == permission_16):
            user_permission = True
            break

    return user_permission

async def oauth_check(
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
        url = DISCORD_BASE_URL + '/users/@me', 
        headers = { 
            'Authorization': f'Bearer {access_token}' 
        }
    )
    if oauth_data.get('message') == '401: Unauthorized':
        return False
    else:
        return True

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

# 復号化関数
async def decrypt_password(encrypted_password:bytes) -> str:
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        decrypted_password = cipher_suite.decrypt(encrypted_password)
        return decrypted_password.decode('utf-8')
    # トークンが無効の場合
    except:
        return ''

# 暗号化関数
async def encrypt_password(password:str) -> bytes:
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        encrypted_password = cipher_suite.encrypt(password.encode('utf-8'))
        return encrypted_password
    except:
        return b''