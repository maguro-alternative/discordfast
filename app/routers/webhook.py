from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request
)

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

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/guild/{guild_id}/webhook')
async def webhook(
    request:Request,
    guild_id:int    
):
    TABLE = 'guild_webhook'

    # データベースへ接続
    await db.connect()

    # テーブルの中身を取得
    table_fetch = await db.select_rows(
        table_name=TABLE,
        columns=[],
        where_clause={}
    )

    if len(table_fetch) != 0:
        if table_fetch[0] == f"{TABLE} does not exist":
            await db.create_table(
                table_name=TABLE,
                columns={
                    'webhook_id': 'NUMERIC PRIMARY KEY', 
                    'channel_id': 'NUMERIC[]', 
                    'channel_type': 'VARCHAR(50)[]',
                    'message_type': 'VARCHAR(50)[]',
                    'message_bot': 'boolean',
                    'channel_nsfw': 'boolean'
                }
            )
            await db.disconnect()
            return templates.TemplateResponse(
                "webhook.html",
                {
                    "request": request, 
                    "title": request.session["user"]['username']
                }
            )
        
    await db.disconnect()
