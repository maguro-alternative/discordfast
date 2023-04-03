from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse,RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB

DISCORD_BASE_URL = "https://discord.com/api"

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

@router.post('/api/line-post-success')
async def line_post_success(request: Request):
    TABLE = 'guilds_ng_channel'

    form = await request.form()

    channel_list = []

    for i in range(1,int(form["count_channel"])):
        form_channel = form.get(f"channel_{i}")
        if form_channel != None:
            channel_list.append(form_channel)

    row_values = { 
        'channel_id': channel_list
    }

    channel_type = []
    
    # チャンネル種類一覧
    if form.get('text_channel') != None:
        channel_type.append(form.get('text_channel'))
    if form.get('voice_channel') != None:
        channel_type.append(form.get('voice_channel'))

    row_values['channel_type'] = channel_type

    message_type = []

    # メッセージの種類
    if form.get('default') != None:
        message_type.append(form.get('default'))
    if form.get('recipient_add') != None:
        message_type.append(form.get('recipient_add'))
    if form.get('pins_add') != None:
        message_type.append(form.get('pins_add'))
    
    row_values['message_type'] = message_type

    # botのメッセージを送信するか
    if form.get('message_bot') != None:
        row_values['message_bot'] = True
    else:
        # しない場合
        row_values['message_bot'] = False

    # 職場閲覧注意チャンネルを送信するか
    if form.get('message_nsfw') != None:
        row_values['channel_nsfw'] = True
    else:
        # しない場合
        row_values['channel_nsfw'] = False

    where_clause = {
        'guild_id': form['guild_id']
    }
    await db.connect()
    await db.update_row(
        table_name=TABLE,
        row_values=row_values,
        where_clause=where_clause
    )
    await db.disconnect()

    return templates.TemplateResponse(
        'linepostsuccess.html',
        {
            'request': request,
            'guild_id': form['guild_id'],
            'title':'成功'
        }
    )