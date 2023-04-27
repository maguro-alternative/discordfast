from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

import aiofiles
import asyncio

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict,Any
from itertools import groupby,chain
import pickle
import io

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    check_permission
)

from message_type.discord_type.message_creater import ReqestDiscord

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

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

@router.get('/guild/{guild_id}/line-post')
async def line_post(
    request:Request,
    guild_id:int
):
    # 使用するデータベースのテーブル名
    TABLE = f'guilds_line_channel_{guild_id}'

    # サーバのチャンネル一覧を取得
    all_channel = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    limit = os.environ.get('USER_LIMIT',default=100)

    # サーバのメンバー一覧を取得
    guild_members = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members?limit={limit}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # 親カテゴリー格納用
    position = []
    # ソート後のチャンネル一覧
    all_channel_sort = []

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

    # サーバの情報を取得
    guild = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # Discordサーバー内での権限をチェック(この場合管理者かどうか)
    permission_bool = await check_permission(
        guild_id=guild_id,
        user_id=request.session["user"]["id"],
        access_token=request.session["oauth_data"]["access_token"],
        permission_16=0x00000008
    )

    user_permission:str = 'normal'

    # 管理者の場合adminを代入
    if permission_bool == True:
        user_permission = 'admin'

    # キャッシュ読み取り
    async with aiofiles.open(
        file=f'{TABLE}.pickle',
        mode='rb'
    ) as f:
        pickled_bytes = await f.read()
        with io.BytesIO() as f:
            f.write(pickled_bytes)
            f.seek(0)
            table_fetch:List[Dict[str,Any]] = pickle.load(f)

    line_row = {}

    for table in table_fetch:
        channel_id:int = table.get('channel_id')
        line_ng_channel:bool = table.get('line_ng_channel')
        ng_message_type:List[str] = table.get('ng_message_type')
        message_bot:bool = table.get('message_bot')
        ng_users:List[int] = table.get('ng_users')

        line_row.update(
            {
                str(channel_id):{
                    'line_ng_channel':line_ng_channel,
                    'ng_message_type':ng_message_type,
                    'message_bot':message_bot,
                    'ng_users':ng_users
                }
            }
        )

    return templates.TemplateResponse(
        "linepost.html",
        {
            "request": request, 
            "guild": guild,
            "guild_id": guild_id,
            "guild_members":guild_members,
            "all_channel": all_channel_sort,
            "line_row":line_row,
            "user_permission":user_permission,
            "title": request.session["user"]['username']
        }
    )