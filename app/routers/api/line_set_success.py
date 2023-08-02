from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import pickle_write,encrypt_password
from core.db_pickle import *
from routers.api.chack.post_user_check import user_checker
from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

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

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class LineSetSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/line-set-success')
        async def line_set_success(request: Request):

            form = await request.form()

            # OAuth2トークンが有効かどうか判断
            check_code = await user_checker(
                request=request,
                oauth_session=DiscordOAuthData(**request.session.get('discord_oauth_data')),
                user_session=DiscordUser(**request.session.get('discord_user'))
            )

            if check_code == 302:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            elif check_code == 400:
                return JSONResponse(content={"message": "Fuck You. You are an idiot."})

            TABLE = f'line_bot'

            hashed_notify_token:bytes = await encrypt_password(form.get('line_notify_token'))
            hashed_bot_token:bytes = await encrypt_password(form.get('line_bot_token'))
            hashed_bot_secret:bytes = await encrypt_password(form.get('line_bot_secret'))
            hashed_group_id:bytes = await encrypt_password(form.get('line_group_id'))
            hashed_client_id:bytes = await encrypt_password(form.get('line_client_id'))
            hashed_client_secret:bytes = await encrypt_password(form.get('line_client_secret'))
            default_channel_id:int = form.get('default_channel_id')
            debug_mode:bool = bool(form.get('debug_mode',default=False))

            row_values = {
                'line_notify_token':hashed_notify_token,
                'line_bot_token':hashed_bot_token,
                "line_bot_secret":hashed_bot_secret,
                'line_group_id':hashed_group_id,
                'line_client_id': hashed_client_id,
                'line_client_secret': hashed_client_secret,
                'default_channel_id':default_channel_id,
                'debug_mode':debug_mode
            }

            await db.connect()
            await db.update_row(
                table_name=TABLE,
                row_values=row_values,
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
