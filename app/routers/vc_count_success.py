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


@router.post('/api/vc-count-success')
async def line_post(
    request:Request
):
    # 使用するデータベースのテーブル名
    TABLE = 'guilds_ng_channel'

    form = await request.form()

    return {"request":form}
