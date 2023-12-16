from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from typing import Dict,List

from pkg.aio_req import (
    aio_get_request,
    aio_post_request
)
from pkg.crypt import decrypt_password

from discord.ext import commands

from core.start import DBot
from core.db_create import DB
from model_types.table_type import LineBotColunm
from model_types.line_type.line_oauth import LineOAuthData
from model_types.environ_conf import EnvConf

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL

LINE_REDIRECT_URI = EnvConf.LINE_CALLBACK_URL
LINE_OAUTH_BASE_URL = EnvConf.LINE_OAUTH_BASE_URL

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class CallBack(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/discord-callback/')
        async def discord_callback(
            code    : str,
            state   : str,
            request : Request
        ):
            # セッションの初期化
            if request.session.get('discord_user') != None:
                request.session.pop("discord_user")
            if request.session.get('discord_connection') != None:
                request.session.pop("discord_connection")
            if request.session.get("discord_oauth_data") != None:
                request.session.pop("discord_oauth_data")

            print(request.session.get("state") , state)
            # stateが一緒しない場合、400で終了
            if request.session.get("state") != state:
                request.session.pop("state")
                raise HTTPException(status_code=400, detail="認証失敗")
            # stateが一致した場合、削除して続行
            else:
                request.session.pop("state")

            authorization_code = code

            request_postdata = {
                'client_id'     : EnvConf.DISCORD_CLIENT_ID,
                'client_secret' : EnvConf.DISCORD_CLIENT_SECRET,
                'grant_type'    : 'authorization_code',
                'code'          : authorization_code,
                'redirect_uri'  : EnvConf.DISCORD_CALLBACK_URL,
            }

            responce_json = await aio_post_request(
                url=f'{DISCORD_BASE_URL}/oauth2/token',
                data=request_postdata,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )

            request.session["discord_oauth_data"] = responce_json

            request.session["discord_user"] = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/users/@me',
                headers={
                    'Authorization': f'Bearer {responce_json["access_token"]}'
                }
            )

            if request.session.get('discord_react'):
                return RedirectResponse(url=f'{EnvConf.REACT_URL}/guilds')
            else:
                # ホームページにリダイレクトする
                return RedirectResponse(url="/guilds")

        @self.router.get("/line-callback/")
        async def line_callback(
            code    : str,
            state   : str,
            request : Request
        ):
            if DB.conn == None:
                await DB.connect()

            print(request.session.get("state") , state)
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
            line_bot_table:List[Dict] = await DB.select_rows(
                table_name='line_bot',
                columns=[],
                where_clause={
                    'guild_id':int(guild_id)
                }
            )

            line_client = LineBotColunm(**line_bot_table[0])

            # 復号化
            client_id:str = await decrypt_password(encrypted_password=line_client.line_client_id)
            client_secret:str = await decrypt_password(encrypted_password=line_client.line_client_secret)

            request_postdata = {
                'client_id'     : client_id,
                'client_secret' : client_secret,
                'grant_type'    : 'authorization_code',
                'code'          : authorization_code,
                'redirect_uri'  : LINE_REDIRECT_URI
            }

            # ログインユーザのアクセストークンを取得
            line_access_token:Dict = await aio_post_request(
                url=f"{LINE_OAUTH_BASE_URL}/token",
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data=request_postdata
            )

            oauth_data = LineOAuthData(**line_access_token)

            id_data = {
                'id_token'  : oauth_data.id_token,
                'client_id' : client_id,
                'nonce'     : nonce
            }

            # idトークンを取得
            line_id_token:Dict = await aio_post_request(
                url=f"{LINE_OAUTH_BASE_URL}/verify",
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data=id_data
            )

            request.session.pop("state")
            request.session.pop("nonce")

            # idトークンが正しくない場合
            if line_id_token.get('error_description') != None:
                raise HTTPException(status_code=400, detail="認証失敗")

            # セッションに認証情報を代入
            request.session['line_oauth_data'] = line_access_token
            request.session['line_user'] = line_id_token

            if request.session.get('line_react'):
                return RedirectResponse(url=f'{EnvConf.REACT_URL}/group/{guild_id}')
            else:
                # ホームページにリダイレクトする
                return RedirectResponse(url=f"/group/{guild_id}")