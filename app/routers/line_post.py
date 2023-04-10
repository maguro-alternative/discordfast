from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List
from itertools import groupby,chain

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    check_permission
)

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
    TABLE = 'guilds_ng_channel'

    # サーバのチャンネル一覧を取得
    all_channel = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
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

    # データベースへ接続
    await db.connect()

    # テーブルの中身を取得
    table_fetch = await db.select_rows(
        table_name=TABLE,
        columns=['guild_id'],
        where_clause={'guild_id':guild_id}
    )

    # リストが空でなく、テーブルが存在しない場合は作成
    if len(table_fetch) != 0:
        if table_fetch[0] == f"{TABLE} does not exist":
            await db.create_table(
                table_name=TABLE,
                columns={
                    'guild_id': 'NUMERIC PRIMARY KEY', 
                    'channel_id': 'NUMERIC[]', 
                    'channel_type': 'VARCHAR(50)[]',
                    'message_type': 'VARCHAR(50)[]',
                    'message_bot': 'boolean',
                    'channel_nsfw': 'boolean'
                }
            )
            await db.disconnect()
            return templates.TemplateResponse(
                "linepost.html",
                {
                    "request": request, 
                    "guild_id": guild_id,
                    "all_channel": all_channel_sort,
                    "ng_channel": [],
                    'channel_type': [],
                    'message_type': [],
                    'message_bot': False,
                    'channel_nsfw': False,
                    "title": request.session["user"]['username']
                }
            )

    # テーブルはあるが中身が空の場合
    if len(table_fetch) == 0:
        row_values = {
            'guild_id': guild_id, 
            'channel_id': [], 
            'channel_type': [],
            'message_type': [],
            'message_bot': True,
            'channel_nsfw': False
        }

        # サーバー用に新たにカラムを作成
        await db.insert_row(
            table_name=TABLE,
            row_values=row_values
        )
        channel_type = []
        message_type = []
        message_bot = False
        channel_nsfw = False

        ng_channel = []
    else:
        # 指定したサーバーのカラムを取得する
        table_fetch = await db.select_rows(
            table_name=TABLE,
            columns=None,
            where_clause={'guild_id':guild_id}
        )
        if ('channel_type' in table_fetch[0]):
            channel_type = table_fetch[0]['channel_type']
        else:
            channel_type = []

        if ('message_type' in table_fetch[0]):
            message_type = table_fetch[0]['message_type']
        else:
            message_type = []

        if ('message_bot' in table_fetch[0]):
            message_bot = table_fetch[0]['message_bot']
        else:
            message_bot = False

        if ('channel_nsfw' in table_fetch[0]):
            channel_nsfw = table_fetch[0]['channel_nsfw']
        else:
            channel_nsfw = False

        ng_channel = [str(i) for i in table_fetch[0]['channel_id']]

    await db.disconnect()

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

    return templates.TemplateResponse(
        "linepost.html",
        {
            "request": request, 
            "guild": guild,
            "guild_id": guild_id,
            "all_channel": all_channel_sort,
            "ng_channel": ng_channel,
            'channel_type': channel_type,
            'message_type': message_type,
            'message_bot': message_bot,
            'channel_nsfw': channel_nsfw,
            "user_permission":user_permission,
            "title": request.session["user"]['username']
        }
    )