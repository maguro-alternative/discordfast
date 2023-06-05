from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates


from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict,Any
from itertools import groupby,chain
from cryptography.fernet import Fernet

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    pickle_read,
    return_permission,
    oauth_check
)
from routers.session_base.user_session import OAuthData,User

from message_type.discord_type.message_creater import ReqestDiscord
from base.guild_permission import Permission

DISCORD_BASE_URL = "https://discord.com/api"
REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]


USER = os.getenv('PGUSER')
PASSWORD = os.getenv('PGPASSWORD')
DATABASE = os.getenv('PGDATABASE')
HOST = os.getenv('PGHOST')
db = PostgresDB(
    user=USER,
    password=PASSWORD,
    database=DATABASE,
    host=HOST
)

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guild/{guild_id}/line-set')
async def line_set(
    request:Request,
    guild_id:int
):
    # OAuth2トークンが有効かどうか判断
    if request.session.get('oauth_data'):
        oauth_session = OAuthData(**request.session.get('oauth_data'))
        user_session = User(**request.session.get('user'))
        # トークンの有効期限が切れていた場合、再ログインする
        if not await oauth_check(access_token=oauth_session.access_token):
            return RedirectResponse(url=REDIRECT_URL,status_code=302)
    else:
        return RedirectResponse(url=REDIRECT_URL,status_code=302)
    
    # 使用するデータベースのテーブル名
    TABLE = f'line_bot'

    # サーバのチャンネル一覧を取得
    all_channel = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ソート後のチャンネル一覧
    all_channel_sort = await sort_discord_channel(all_channel=all_channel)

    # サーバの情報を取得
    guild = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ログインユーザの情報を取得
    guild_user = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{user_session.id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )
    role_list = [
        g 
        for g in guild_user["roles"]
    ]

    # サーバの権限を取得
    guild_user_permission = await return_permission(
        guild_id=guild_id,
        user_id=user_session.id,
        access_token=oauth_session.access_token
    )

    # パーミッションの番号を取得
    permission_code = await guild_user_permission.get_permission_code()

    # キャッシュ読み取り
    guild_table_fetch:List[Dict[str,Any]] = await pickle_read(filename='guild_set_permissions')
    
    guild_table = [
        g 
        for g in guild_table_fetch 
        if int(g.get('guild_id')) == guild_id
    ]
    guild_permission_code = 8
    guild_permission_user = list()
    guild_permission_role = list()
    if len(guild_table) > 0:
        guild_permission_code = int(guild_table[0].get('line_bot_permission'))
        guild_permission_user = [
            user 
            for user in guild_table[0].get('line_bot_user_id_permission')
        ]
        guild_permission_role = [
            role
            for role in guild_table[0].get('line_bot_role_id_permission')
        ]

    and_code = guild_permission_code & permission_code
    admin_code = 8 & permission_code
    user_permission:str = 'normal'

    # 許可されている場合、管理者の場合
    if (and_code == permission_code or 
        admin_code == 8 or
        user_session.id in guild_permission_user or
        len(set(guild_permission_role) & set(role_list)) > 0
        ):
        user_permission = 'admin'

    # キャッシュ読み取り
    table_fetch:List[Dict[str,Any]] = await pickle_read(filename=TABLE)

    line_row = {}

    # 各項目をフロント部分に渡す
    for table in table_fetch:
        if int(table.get('guild_id')) == guild_id:
            line_notify_token:str = await decrypt_password(encrypted_password=bytes(table.get('line_notify_token')))
            line_bot_token:str = await decrypt_password(encrypted_password=bytes(table.get('line_bot_token')))
            line_bot_secret:str = await decrypt_password(encrypted_password=bytes(table.get('line_bot_secret')))
            line_group_id:str = await decrypt_password(encrypted_password=bytes(table.get('line_group_id')))
            default_channel_id:int = table.get('default_channel_id')
            debug_mode:bool = bool(table.get('debug_mode'))

            line_row = {
                'line_notify_token':line_notify_token,
                'line_bot_token':line_bot_token,
                'line_bot_secret':line_bot_secret,
                'line_group_id':line_group_id,
                'default_channel_id':default_channel_id,
                'debug_mode':debug_mode
            }


    return templates.TemplateResponse(
        "guild/line/lineset.html",
        {
            "request": request, 
            "guild": guild,
            "guild_id": guild_id,
            "all_channel": all_channel_sort,
            "line_row":line_row,
            "user_permission":user_permission,
            "title": "LINEBOTおよびグループ設定/" + guild['name']
        }
    )
    

# 復号化関数
async def decrypt_password(encrypted_password:bytes) -> str:
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        decrypted_password = cipher_suite.decrypt(encrypted_password)
        return decrypted_password.decode('utf-8')
    # トークンが無効の場合
    except:
        return ''


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