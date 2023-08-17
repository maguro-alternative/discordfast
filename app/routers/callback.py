from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()


import urllib.parse
from cryptography.fernet import Fernet

import os
import secrets
from typing import Dict,List

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    aio_post_request,
    pickle_read,
    encrypt_password,
    decrypt_password
)

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import db
    from model_types.discord_type.discord_user_session import DiscordOAuthData
    from model_types.table_type import LineBotColunm
    from model_types.line_type.line_oauth import (
        LineCallbackRequest,
        LineOAuthData,
        LineIdTokenResponse
    )
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import db
    from app.model_types.discord_type.discord_user_session import DiscordOAuthData
    from app.model_types.table_type import LineBotColunm
    from app.model_types.line_type.line_oauth import (
        LineCallbackRequest,
        LineOAuthData,
        LineIdTokenResponse
    )

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

LINE_REDIRECT_URI = os.environ.get('LINE_CALLBACK_URL')
LINE_REDIRECT_URI_ENCODE = urllib.parse.quote(LINE_REDIRECT_URI)
LINE_OAUTH_BASE_URL = "https://api.line.me/oauth2/v2.1"

ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class CallBack(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/discord-callback/')
        async def discord_callback(
            code:str,
            state: str,
            request:Request
        ):
            # セッションの初期化
            if request.session.get('discord_user') != None:
                request.session.pop("discord_user")
            if request.session.get('discord_connection') != None:
                request.session.pop("discord_connection")
            if request.session.get("discord_oauth_data") != None:
                request.session.pop("discord_oauth_data")

            # stateが一緒しない場合、400で終了
            if request.session.get("state") != state:
                raise HTTPException(status_code=400, detail="認証失敗")
            # stateが一致した場合、削除して続行
            else:
                request.session.pop("state")

            authorization_code = code

            request_postdata = {
                'client_id': os.environ.get('DISCORD_CLIENT_ID'),
                'client_secret': os.environ.get('DISCORD_CLIENT_SECRET'),
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': os.environ.get('DISCORD_CALLBACK_URL')
            }

            responce_json = await aio_post_request(
                url = DISCORD_BASE_URL + '/oauth2/token',
                data = request_postdata,
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            request.session["discord_oauth_data"] = responce_json

            request.session["discord_user"] = await aio_get_request(
                url = DISCORD_BASE_URL + '/users/@me',
                headers = {
                    'Authorization': f'Bearer {responce_json["access_token"]}'
                }
            )

            # ホームページにリダイレクトする
            return RedirectResponse(url="/guilds")

        @self.router.get("/line-callback/")
        async def line_callback(
            code:str,
            state: str,
            request:Request
        ):
            # stateが一緒しない場合、400で終了
            if request.session.get("state") != state:
                request.session.pop("state")
                request.session.pop("nonce")
                request.session.pop('guild_id')
                raise HTTPException(status_code=400, detail="認証失敗")


            authorization_code = code
            nonce = request.session.get("nonce")

            guild_id = request.session.get('guild_id')

            # line_botテーブルの読み込み
            line_bot_table:List[Dict] = await pickle_read(filename="line_bot")

            guild_set_line_bot:List[Dict] = [
                line
                for line in line_bot_table
                if int(line.get('guild_id')) == int(guild_id)
            ]

            # 復号化
            client_id:str = await decrypt_password(encrypted_password=bytes(guild_set_line_bot[0].get('line_client_id')))
            client_secret:str = await decrypt_password(encrypted_password=bytes(guild_set_line_bot[0].get('line_client_secret')))

            request_postdata = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': LINE_REDIRECT_URI
            }

            # ログインユーザのアクセストークンを取得
            line_access_token:Dict = await aio_post_request(
                url=f"{LINE_OAUTH_BASE_URL}/token",
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data = request_postdata
            )

            id_data = {
                'id_token':line_access_token.get('id_token'),
                'client_id': client_id,
                'nonce':nonce
            }

            # idトークンを取得
            line_id_token:Dict = await aio_post_request(
                url=f"{LINE_OAUTH_BASE_URL}/verify",
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data = id_data
            )

            request.session.pop("state")
            request.session.pop("nonce")
            #request.session.pop('guild_id')

            # idトークンが正しくない場合
            if line_id_token.get('error_description') != None:
                raise HTTPException(status_code=400, detail="認証失敗")

            # セッションに認証情報を代入
            request.session['line_oauth_data'] = line_access_token
            request.session['line_user'] = line_id_token

            # ホームページにリダイレクトする
            return RedirectResponse(url=f"/group/{guild_id}")

        @self.router.post('/discord-callback/')
        async def discord_react_callback(
            request:Request
        ) -> JSONResponse:
            """
            Discordログイン時のcallback処理

            Args:
                request (Request): 認証時のトークンのみ

            Returns:
                JSONResponse: 暗号化されたアクセストークンが返却
            """
            request_postdata = {
                'client_id'     : os.environ.get('DISCORD_CLIENT_ID'),
                'client_secret' : os.environ.get('DISCORD_CLIENT_SECRET'),
                'grant_type'    : 'authorization_code',
                'code'          : request.get('code'),
                'redirect_uri'  : os.environ.get('DISCORD_CALLBACK_URL')
            }

            # アクセストークンを取得
            responce_json = await aio_post_request(
                url = DISCORD_BASE_URL + '/oauth2/token',
                data = request_postdata,
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            oauth_data = DiscordOAuthData(**responce_json)

            access_token:bytes = await encrypt_password(encrypted_password=oauth_data.access_token)
            json_content = {
                'accessToken':access_token.decode('utf-8')
            }

            return JSONResponse(content=json_content)

        @self.router.post("/line-callback/")
        async def line_react_callback(
            request:LineCallbackRequest
        ) -> JSONResponse:
            """
            LINEログイン時のcallback処理

            Args:
                request (LineCallbackRequest): 送られるボディデータ

            Raises:
                HTTPException: 認証失敗時400エラー

            Returns:
                JSONResponse: 暗号化されたアクセストークン、ユーザid、ユーザ名
            """
            if db.conn == None:
                await db.connect()

            line_bot_info = await db.select_rows(
                table_name="line_bot",
                columns=[],
                where_clause={
                    'guild_id':request.guild_id
                }
            )
            line_client = LineBotColunm(**line_bot_info[0])

            # 復号化
            client_id:str = await decrypt_password(encrypted_password=bytes(line_client.line_client_id))
            client_secret:str = await decrypt_password(encrypted_password=bytes(line_client.line_client_secret))
            request_postdata = {
                'client_id'     : client_id,
                'client_secret' : client_secret,
                'grant_type'    : 'authorization_code',
                'code'          : request.code,
                'redirect_uri'  : LINE_REDIRECT_URI
            }

            # ログインユーザのアクセストークンを取得
            line_access_token:Dict = await aio_post_request(
                url=f"{LINE_OAUTH_BASE_URL}/token",
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data = request_postdata
            )

            oauth_data = LineOAuthData(**line_access_token)

            id_data = {
                'id_token'  : oauth_data.id_token,
                'client_id' : client_id,
                'nonce'     : request.nonce
            }

            # idトークンを取得
            line_id_token:Dict = await aio_post_request(
                url=f"{LINE_OAUTH_BASE_URL}/verify",
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data = id_data
            )

            # idトークンが正しくない場合
            if line_id_token.get('error_description') != None:
                raise HTTPException(status_code=400, detail="認証失敗")

            line_id_response = LineIdTokenResponse(**line_id_token)

            access_token:bytes = await encrypt_password(encrypted_password=oauth_data.access_token)

            line_user_name:bytes = await encrypt_password(encrypt_password=line_id_response.name)
            line_user_id:bytes = await encrypt_password(encrypt_password=line_id_response.sub)

            json_contents = {
                'AccessToken'   :access_token.decode('utf-8'),
                'lineUserName'  :line_user_name.decode('utf-8'),
                'lineUserId'    :line_user_id.decode('utf-8')
            }

            return JSONResponse(content=json_contents)