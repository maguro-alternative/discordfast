from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
import re
from cryptography.fernet import Fernet

from base.database import PostgresDB
from base.aio_req import pickle_write
from core.db_pickle import *
from routers.api.chack.post_user_check import user_checker
from routers.session_base.user_session import DiscordOAuthData,DiscordUser

from core.pickes_save.line_bot_columns import LINE_BOT_COLUMNS

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"
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

@router.post('/api/line-group-success')
async def line_group_success(request: Request):

    TABLE = "line_bot"

    form = await request.form()
    default_channel_id:int = int(form.get('default_channel_id'))

    await db.connect()
    await db.update_row(
        table_name=TABLE,
        row_values={
            'default_channel_id':default_channel_id
        },
        where_clause={
            'guild_id':form.get('guild_id')
        }
    )
    # 更新後のテーブルを取得
    table_fetch = await db.select_rows(
        table_name=TABLE,
        columns=[],
        where_clause={}
    )
    await db.disconnect()

    # pickleファイルに書き込み
    await pickle_write(
        filename=TABLE,
        table_fetch=table_fetch
    )

    return templates.TemplateResponse(
        'api/linesetsuccess.html',
        {
            'request': request,
            'guild_id': form['guild_id'],
            'title':'成功'
        }
    )