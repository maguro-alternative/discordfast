from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse,RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request
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
                    "all_channel": all_channel,
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

    return templates.TemplateResponse(
        "linepost.html",
        {
            "request": request, 
            "guild": guild,
            "guild_id": guild_id,
            "all_channel": all_channel,
            "ng_channel": ng_channel,
            'channel_type': channel_type,
            'message_type': message_type,
            'message_bot': message_bot,
            'channel_nsfw': channel_nsfw,
            "title": request.session["user"]['username']
        }
    )