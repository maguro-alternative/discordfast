from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from fastapi.responses import JSONResponse

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    aio_post_request,
    check_permission
)

from core.db_pickle import *

import aiofiles
import pickle

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

@router.post('/api/webhook-post')
async def line_post(
    request:Request
):
    """
    event_json
    {
        'webhook_id':int,
        'webhook_name':str,
        'webhook_icon_url':str,
        'content':str
    }
    """
    event_json = await request.json()

    webhook_id = event_json.get('webhook_id')

    webhook_obj = await aio_get_request(
        url = DISCORD_BASE_URL + f'/webhooks/{webhook_id}',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    webhook_token = webhook_obj.get('token')

    content_data = {'content':event_json.get('content')}

    if event_json.get('webhook_name') != None:
        content_data.update({
            'username': event_json.get('webhook_name')
        })

    if event_json.get('webhook_icon_url') != None:
        content_data.update({
            'avatar_url': event_json.get('webhook_icon_url')
        })

    await aio_post_request(
        url = DISCORD_BASE_URL + f'/webhooks/{webhook_id}/{webhook_token}',
        headers={'Content-Type': 'application/json'}
    )

    return JSONResponse(status_code=200,content={'response':'ok'})
