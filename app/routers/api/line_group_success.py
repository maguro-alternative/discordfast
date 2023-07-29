from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import pickle_write,pickle_read,decrypt_password
from core.db_pickle import *

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

from message_type.line_type.line_message import LineBotAPI
from message_type.discord_type.message_creater import ReqestDiscord

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

class LineGroupSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/line-group-success')
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

            # LINE Botのトークンなどを取り出す
            line_bot_fetch:List[dict] = await pickle_read(filename='line_bot')

            bot_info:List[dict] = [
                bot
                for bot in line_bot_fetch
                if int(bot.get('guild_id')) == int(form.get('guild_id'))
            ]

            line_notify_token:str = await decrypt_password(encrypted_password=bytes(bot_info[0].get('line_notify_token')))
            line_bot_token:str = await decrypt_password(encrypted_password=bytes(bot_info[0].get('line_bot_token')))

            line_group_id:str = await decrypt_password(encrypted_password=bytes(bot_info[0].get('line_group_id')))

            # LINEのインスタンスを作成
            line_bot_api = LineBotAPI(
                notify_token = line_notify_token,
                line_bot_token = line_bot_token,
                line_group_id = line_group_id
            )

            # Discordのインスタンスを作成
            discord_bot_api = ReqestDiscord(
                guild_id=int(form.get('guild_id')),
                limit=100,
                token=os.environ["DISCORD_BOT_TOKEN"]
            )

            # LINEのユーザ名
            user_name:str = request.session['line_user']['name']
            # Discordのチャンネル名
            default_channel_info = await discord_bot_api.channel_info_get(
                channel_id=default_channel_id
            )

            # 変更URL
            url = (os.environ.get('LINE_CALLBACK_URL').replace('/line-callback/','')) + f'/group/{form.get("guild_id")}'

            change_text = f"{user_name}によりDiscordへの送信先が「{default_channel_info.name}」に変更されました。"
            change_text += f"\n変更はこちらから\n{url}"

            # 通知するチェックボックスが入っていた場合
            if form.get('chenge_alert') != None:
                # LINEとDiscord双方に変更を送信
                await line_bot_api.push_message_notify(
                    message=change_text
                )
                await discord_bot_api.send_discord(
                    channel_id=default_channel_id,
                    message=change_text
                )

            return templates.TemplateResponse(
                'api/linesetsuccess.html',
                {
                    'request': request,
                    'guild_id': form['guild_id'],
                    'title':'成功'
                }
            )
