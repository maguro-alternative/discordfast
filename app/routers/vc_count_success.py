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
    TABLE = 'guilds_vc_signal'

    form = await request.form()

    # "send_channel_id_"で始まるキーのみを抽出し、数字部分を取得する
    numbers = [
        int(key.replace("send_channel_id_", "")) 
        for key in form.keys() 
        if key.startswith("send_channel_id_")
    ]

    await db.connect()

    # チャンネルごとに更新をかける
    for vc_id in numbers:
        join_bot = False
        everyone_mention = False
        role_key = [
            int(form.get(key))
            for key in form.keys()
            if key.startswith(f"role_{vc_id}_")
        ]

        if form.get(f"join_bot_{vc_id}") != None:
            join_bot = True
        if form.get(f"everyone_mention_{vc_id}") != None:
            everyone_mention = True
            
        row_values = {
            'send_channel_id':form.get(f"send_channel_id_{vc_id}"),
            'join_bot':join_bot,
            'everyone_mention':everyone_mention,
            'mention_role_id':role_key
        }

        where_clause = {
            'vc_id': vc_id
        }

        await db.update_row(
            table_name=TABLE,
            row_values=row_values,
            where_clause=where_clause
        )

    await db.disconnect()

    return templates.TemplateResponse(
        'vccountsuccess.html',
        {
            'request': request,
            'guild_id': form['guild_id'],
            'title':'成功'
        }
    )
