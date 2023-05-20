from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import pickle_write
from base.aio_req import (
    return_permission,
    oauth_check
)
REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"


from core.db_pickle import *


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
    form = await request.form()

    # OAuth2トークンが有効かどうか判断
    try:
        await return_permission(
            guild_id=form["guild_id"],
            user_id=request.session["user"]["id"],
            access_token=request.session["oauth_data"]["access_token"]
        )
        if not await oauth_check(access_token=request.session["oauth_data"]["access_token"]):
            return RedirectResponse(url=REDIRECT_URL,status_code=302)
    except KeyError:
        return RedirectResponse(url=REDIRECT_URL,status_code=302)

    # 使用するデータベースのテーブル名
    TABLE = f'guilds_vc_signal_{form.get("guild_id")}'

    # "send_channel_id_"で始まるキーのみを抽出し、数字部分を取得する
    numbers = [
        int(key.replace("send_channel_id_", "")) 
        for key in form.keys() 
        if key.startswith("send_channel_id_")
    ]

    row_list = []

    # チャンネルごとに更新をかける
    for vc_id in numbers:
        row_values = {}
        send_signal = False
        join_bot = False
        everyone_mention = False
        role_key = [
            int(form.get(key))
            for key in form.keys()
            if key.startswith(f"role_{vc_id}_")
        ]

        if form.get(f"send_signal_{vc_id}") != None:
            send_signal = True
        if form.get(f"join_bot_{vc_id}") != None:
            join_bot = True
        if form.get(f"everyone_mention_{vc_id}") != None:
            everyone_mention = True
            
        row_values = {
            'send_signal':send_signal,
            'send_channel_id':form.get(f"send_channel_id_{vc_id}"),
            'join_bot':join_bot,
            'everyone_mention':everyone_mention,
            'mention_role_id':role_key
        }

        where_clause = {
            'vc_id': vc_id
        }

        row_list.append({
            'where_clause':where_clause,
            'row_values':row_values
        })

    #print(row_list)

    await db.connect()

    await db.primary_batch_update_rows(
        table_name=TABLE,
        set_values_and_where_columns=row_list,
        table_colum=VC_COLUMNS
    )

    # 更新後のテーブルを取得
    table_fetch = await db.select_rows(
        table_name=TABLE,
        columns=[],
        where_clause={}
    )

    await db.disconnect()

    #print(table_fetch)

    # pickleファイルに書き込み
    await pickle_write(
        filename=TABLE,
        table_fetch=table_fetch
    )

    return templates.TemplateResponse(
        'vccountsuccess.html',
        {
            'request': request,
            'guild_id': form['guild_id'],
            'title':'成功'
        }
    )
