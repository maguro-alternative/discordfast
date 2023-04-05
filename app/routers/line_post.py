from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse,RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

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

    position = []
    channel_position = {}

    all_channel_sort = []

    # 順序がバラバラなのでアプリと同様の並びにソート
    for all in all_channel:
        # 親チャンネルがすでに連想配列として定義されているか、また親チャンネルではないか
        if str(all.get('parent_id')) in channel_position and all.get('type') != 4:
            channel_position[str(all.get('parent_id'))].append(all)
        # 親チャンネルの場合
        elif all.get('type') == 4:
            position.append(all)
        # 親チャンネルが存在しない場合
        else:
            channel_position[str(all.get('parent_id'))] = [all]
            if str(all.get('parent_id')) == 'None':
                position.append(all)

    for po_id in position:
        all_channel_sort.append(po_id)
        for i in range(0,len(channel_position.get(str(po_id['id']),[]))):
            all_channel_sort.append(channel_position[str(po_id['id'])][i])

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

    if len(table_fetch) == 0:
        row_values = {
            'guild_id': guild_id, 
            'channel_id': [], 
            'channel_type': [],
            'message_type': [],
            'message_bot': True,
            'channel_nsfw': False
        }

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

    permission_bool = await check_permission(
        guild_id=guild_id,
        user_id=request.session["user"]["id"],
        access_token=request.session["oauth_data"]["access_token"],
        permission_16=0x00000008
    )

    user_permission:str = 'normal'

    if permission_bool == True:
        user_permission = 'admin'
        print('admin')

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