from fastapi import APIRouter,Request
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from pkg.aio_req import aio_get_request
from pkg.crypt import decrypt_password

import urllib.parse

import secrets
from typing import Dict,List
from model_types.table_type import LineBotColunm
from model_types.line_type.line_type import LineBotInfo
from model_types.environ_conf import EnvConf
from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

LINE_REDIRECT_URL = "https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={}&redirect_uri={}&state={}&scope=profile%20openid%20email&nonce={}"
LINE_BASE_URL = EnvConf.LINE_BASE_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN
ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

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


        @self.router.get("/line-login/view")
        async def line_login_select(request: Request):
            if DB.conn == None:
                await DB.connect()

            # line_botテーブルをロード
            line_bot_table:List[Dict] = await DB.select_rows(
                table_name="line_bot",
                columns=[],
                where_clause={}
            )

            # Botが所属しているサーバidを取得
            bot_guild_ids:List[int] = [
                bot_guild.id
                for bot_guild in self.bot.guilds
            ]

            # Botが所属しているサーバからLINEの認証情報があるところ
            line_login_bots:List[LineBotColunm] = [
                LineBotColunm(**guild)
                for guild in line_bot_table
                if (len(guild.get('line_client_id')) > 0 and
                    len(guild.get('line_client_secret')) > 0 and
                    len(guild.get('line_bot_token')) > 0 and
                    int(guild.get('guild_id')) in bot_guild_ids
                    )
            ]

            bot_profiles = list()

            # ログインできるBotをListに並べる
            for line in line_login_bots:
                # トークンを復号
                line_bot_token:str = await decrypt_password(encrypted_password=line.line_bot_token)
                line_clinet_id:str = await decrypt_password(encrypted_password=line.line_client_id)

                # LINEのcallbackurlをエンコードする
                redirect_uri = EnvConf.LINE_CALLBACK_URL
                redirect_encode_uri:str = urllib.parse.quote(redirect_uri)
                # LINEBotの情報を取得
                bot_profile_tmp:Dict = await aio_get_request(
                    url=f"{LINE_BASE_URL}/v2/bot/info",
                    headers={
                        'Authorization' : f'Bearer {line_bot_token}'
                    }
                )
                bot_profile:LineBotInfo = LineBotInfo(**bot_profile_tmp)
                # 識別のためDiscordサーバーのidを追加
                bot_profiles.append({
                    'pictureUrl'            :bot_profile.pictureUrl,
                    'displayName'           :bot_profile.displayName,
                    'clientId'              :line_clinet_id,
                    'redirectEncodeUri'     :redirect_encode_uri,
                    'guildId'               :str(line.guild_id)
                })

            return JSONResponse(content=bot_profiles)


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
                where_clause={
                    'guild_id':guild_id
                }
            )

            # 主キーがサーバーのidと一致するものを取り出す
            guild_set_line_bot:LineBotColunm = LineBotColunm(**line_bot_table[0])

            # クライアントidを復号
            client_id:str = await decrypt_password(encrypted_password=guild_set_line_bot.line_client_id)

            # LINEのcallbackurlをエンコードする
            redirect_uri = EnvConf.LINE_CALLBACK_URL
            redirect_encode_uri = urllib.parse.quote(redirect_uri)

            try:
                oauth_data:Dict = await aio_get_request(
                    url=f'{LINE_BASE_URL}/oauth2/v2.1/verify?access_token={request.session["line_oauth_data"]["access_token"]}',
                    headers={}
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