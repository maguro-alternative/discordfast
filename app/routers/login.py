from fastapi import APIRouter,Request,Header
from fastapi.responses import RedirectResponse,HTMLResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

from base.aio_req import (
    aio_get_request,
    pickle_read,
    decrypt_password
)

from cryptography.fernet import Fernet
import urllib.parse

import os
import secrets
from typing import Dict,List

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import DB

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"
DISCORD_BASE_URL = "https://discord.com/api"

LINE_REDIRECT_URL = "https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={}&redirect_uri={}&state={}&scope=profile%20openid%20email&nonce={}"
LINE_BASE_URL = "https://api.line.me"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]

class Login(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get("/discord-login")
        async def discord_login(request: Request):
            # ランダムなstate値の生成
            state = secrets.token_urlsafe(16)
            request.session['state'] = state
            try:
                oauth_data:dict = await aio_get_request(
                    url=f'{DISCORD_BASE_URL}/users/@me',
                    headers={
                        'Authorization': f'Bearer {request.session["discord_oauth_data"]["access_token"]}' 
                    }
                )
                if oauth_data.get('message') == '401: Unauthorized':
                    return RedirectResponse(url=f"{DISCORD_REDIRECT_URL}&state={state}",status_code=302)
            except KeyError:
                return RedirectResponse(url=f"{DISCORD_REDIRECT_URL}&state={state}",status_code=302)
            return templates.TemplateResponse(
                'register.html',
                {
                    'request': request,
                }
            )

        @self.router.get("/line-login")
        async def line_login_select(request: Request):
            if DB.conn == None:
                await DB.connect()
            # Botが所属しているサーバを取得
            bot_in_guild_get:List[Dict] = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/users/@me/guilds',
                headers={
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # line_botテーブルをロード
            line_bot_table:List[Dict] = await DB.select_rows(
                table_name="line_bot",
                columns=[],
                where_clause={}
            )

            # Botが所属しているサーバidを取得
            bot_guild_ids:List[int] = [
                int(bot_guild.get('id'))
                for bot_guild in bot_in_guild_get
            ]

            # Botが所属しているサーバからLINEの認証情報があるところ
            line_set_guilds:List[Dict] = [
                guild
                for guild in line_bot_table
                if (len(guild.get('line_client_id')) > 0 and
                    len(guild.get('line_client_secret')) > 0 and
                    len(guild.get('line_bot_token')) > 0 and
                    int(guild.get('guild_id')) in bot_guild_ids
                    )
            ]

            bot_profiles = list()

            # ログインできるBotをListに並べる
            for line in line_set_guilds:
                # トークンを復号
                line_bot_token:str = await decrypt_password(encrypted_password=bytes(line.get('line_bot_token')))
                # LINEBotの情報を取得
                bot_profile_tmp:Dict = await aio_get_request(
                    url=f"{LINE_BASE_URL}/v2/bot/info",
                    headers={
                        'Authorization' : f'Bearer {line_bot_token}'
                    }
                )
                # 識別のためDiscordサーバーのidを追加
                bot_profile_tmp.update({
                    'guild_id':line.get('guild_id')
                })
                bot_profiles.append(bot_profile_tmp)

            return templates.TemplateResponse(
                "linelogin.html",
                {
                    "request": request,
                    "bot_profiles":bot_profiles,
                    "title": "LINEログイン選択"
                }
            )


        @self.router.get("/line-login/{guild_id}")
        async def line_login(
            request: Request,
            guild_id: int
        ):
            if DB.conn == None:
                await DB.connect()
            # セッションの初期化
            if request.session.get('line_user') != None:
                request.session.pop("line_user")
            if request.session.get("line_oauth_data") != None:
                request.session.pop("line_oauth_data")


            # ランダムなstate値の生成
            state = secrets.token_urlsafe(16)
            nonce = secrets.token_urlsafe(16)

            request.session['state'] = state
            request.session['nonce'] = nonce
            request.session['guild_id'] = guild_id

            # line_botテーブルをロード
            line_bot_table:List[Dict] = await DB.select_rows(
                table_name="line_bot",
                columns=[],
                where_clause={}
            )

            # 主キーがサーバーのidと一致するものを取り出す
            guild_set_line_bot:List[Dict] = [
                line
                for line in line_bot_table
                if int(line.get('guild_id')) == guild_id
            ]

            # クライアントidを復号
            client_id:str = await decrypt_password(encrypted_password=bytes(guild_set_line_bot[0].get('line_client_id')))

            # LINEのcallbackurlをエンコードする
            redirect_uri = os.environ.get('LINE_CALLBACK_URL')
            redirect_encode_uri = urllib.parse.quote(redirect_uri)

            try:
                oauth_data:Dict = await aio_get_request(
                    url = f'{LINE_BASE_URL}/oauth2/v2.1/verify?access_token={request.session["line_oauth_data"]["access_token"]}', 
                    headers = {}
                )
                if oauth_data.get('error_description') == 'access token expired':
                    return RedirectResponse(url=LINE_REDIRECT_URL.format(client_id,redirect_encode_uri,state,nonce),status_code=302)
            except KeyError:
                return RedirectResponse(url=LINE_REDIRECT_URL.format(client_id,redirect_encode_uri,state,nonce),status_code=302)
            return templates.TemplateResponse(
                'register.html',
                {
                    'request': request,
                }
            )


        @self.router.post("/register")
        async def register_post(request: Request):
            # ホームページにリダイレクトする
            return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)