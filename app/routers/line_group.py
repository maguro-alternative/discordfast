from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    pickle_read,
    sort_discord_channel,
    sort_channels,
    decrypt_password
)

from model_types.line_type.line_request_type import LineBaseRequest
from model_types.line_type.line_oauth import LineTokenVerify,LineProfile
from model_types.table_type import LineBotColunm

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

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

LINE_OAUTH_BASE_URL = "https://api.line.me/oauth2/v2.1"
LINE_BOT_URL = 'https://api.line.me/v2/bot'

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")


class LineGroup(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/group/{guild_id}')
        async def group(
            request:Request,
            guild_id:int
        ):
            # OAuth2トークンが有効かどうか判断
            if request.session.get('line_oauth_data'):
                try:
                    oauth_session = await aio_get_request(
                        url=f"{LINE_OAUTH_BASE_URL}/verify?access_token={request.session['line_oauth_data']['access_token']}",
                        headers={}
                    )
                    # トークンの有効期限が切れていた場合、再ログインする
                    if oauth_session.get('error_description') == 'Invalid IdToken Nonce.':
                        return RedirectResponse(url='/line-login')
                except KeyError:
                    return RedirectResponse(url='/line-login')
            else:
                return RedirectResponse(url='/line-login')

            # line_botテーブルを取得
            line_bot_table:List[Dict] = await pickle_read(filename="line_bot")

            guild_id = request.session.get('guild_id')

            guild_set_line_bot:List[Dict] = [
                line
                for line in line_bot_table
                if int(line.get('guild_id')) == int(guild_id)
            ]

            # 復号化
            line_group_id:str = await decrypt_password(encrypted_password=bytes(guild_set_line_bot[0].get('line_group_id')))
            line_bot_token:str = await decrypt_password(encrypted_password=bytes(guild_set_line_bot[0].get('line_bot_token')))

            # LINE→Discordへの送信先チャンネルid
            default_channel_id:int = int(guild_set_line_bot[0].get('default_channel_id'))

            # グループIDが有効かどうか判断
            r = await aio_get_request(
                url=f"{LINE_BOT_URL}/group/{line_group_id}/member/{request.session['line_user']['sub']}",
                headers={
                    'Authorization': f'Bearer {line_bot_token}'
                }
            )
            # グループIDが無効の場合、友達から判断
            if r.get('message') != None:
                raise HTTPException(status_code=400, detail="認証失敗")

            # サーバのチャンネル一覧を取得
            all_channel = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # ソート後のチャンネル一覧
            all_channel_sort = await sort_discord_channel(all_channel=all_channel)

            # アクティブスレッドを取得
            active_threads = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/threads/active',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # フォーラムチャンネルがあるか調べる
            threads_list = [
                t
                for t in all_channel_sort
                if int(t.get('type')) == 15
            ]

            for a_thead in active_threads.get('threads'):
                all_channel_sort.append(a_thead)

            archived_threads = list()

            for thread in threads_list:
                thread_id = thread.get('id')
                # アーカイブスレッドを取得
                archived_threads = await aio_get_request(
                    url = DISCORD_BASE_URL + f'/channels/{thread_id}/threads/archived/public',
                    headers = {
                        'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                    }
                )
                for a_thead in archived_threads.get('threads'):
                    all_channel_sort.append(a_thead)


            return templates.TemplateResponse(
                "linegroup.html",
                {
                    "request": request, 
                    "guild_id": guild_id,
                    "all_channel": all_channel_sort,
                    "default_channel_id":default_channel_id,
                    "title":f"{request.session['line_user']['name']}のサーバ一覧"
                }
            )

        @self.router.post('/group')
        async def group(
            request:LineBaseRequest
        ):
            if db.conn == None:
                await db.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token:str = await decrypt_password(decrypt_password=request.access_token.encode('utf-8'))
                # Discordのユーザ情報を取得
                line_user = await aio_get_request(
                    url=f"{LINE_OAUTH_BASE_URL}/verify?access_token={access_token}",
                    headers={}
                )
                line_user = LineTokenVerify(**line_user)

                # トークンが無効
                if line_user.error != None:
                    return JSONResponse(content={'message':'access token Unauthorized'})
            else:
                line_user = {
                    'scope'     :'profile%20openid%20email',
                    'client_id' :'0',
                    'expires_in':100
                }
                line_user = LineTokenVerify(**line_user)

            TABLE = 'line_bot'

            for guild in self.bot.guilds:
                if request.guild_id == guild.id:
                    l = await db.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':request.guild_id
                        }
                    )

                    line_bot_table = LineBotColunm(**l[0])

                    # 復号化
                    line_group_id:str = await decrypt_password(encrypted_password=bytes(line_bot_table.line_group_id))
                    line_bot_token:str = await decrypt_password(encrypted_password=bytes(line_bot_table.line_bot_token))

                    # LINE→Discordへの送信先チャンネルid
                    default_channel_id = line_bot_table.default_channel_id

                    # デバッグモード
                    if DEBUG_MODE == False:
                        # グループIDが有効かどうか判断
                        r = await aio_get_request(
                            url=f"{LINE_BOT_URL}/group/{line_group_id}/member/{request.sub}",
                            headers={
                                'Authorization': f'Bearer {line_bot_token}'
                            }
                        )
                        line_group_profile = LineProfile(**r)
                        # グループIDが無効の場合、友達から判断
                        if line_group_profile.message != None:
                            raise HTTPException(status_code=400, detail="認証失敗")
                    else:
                        r = {
                            'displayName'   :'test',
                            'userId'        :'aaa',
                            'pictureUrl'    :'png'
                        }
                        line_group_profile = LineProfile(**r)

                    # カテゴリーごとにチャンネルをソート
                    category_dict,category_index = await sort_channels(channels=guild.channels)

                    channels_json = dict()
                    channels_dict = dict()

                    channels_list = list()
                    category_list = list()

                    for category_id,category_value in category_index.items():
                        # カテゴリーチャンネル一覧
                        category_list.append({
                            'id'    :category_value.id,
                            'name'  :category_value.name
                        })
                        # カテゴリー内のチャンネル一覧
                        channels_list = [
                            {
                                'id'    :chan.id,
                                'name'  :chan.name,
                                'type'  :type(chan).__name__
                            }
                            for chan in category_dict.get(category_id)
                        ]
                        channels_dict.update({
                            category_id:channels_list
                        })
                    # カテゴリーなしのチャンネル一覧
                    channels_dict.update({
                        'None':[
                            {
                                'id'    :chan.id,
                                'name'  :chan.name,
                                'type'  :type(chan).__name__
                            }
                            for chan in category_dict.get('None')
                        ]
                    })

                    # スレッド一覧
                    threads = [
                        {
                            'id'    :thread.id,
                            'name'  :thread.name
                        }
                        for thread in guild.threads
                    ]

                    channels_json.update({
                        'categorys'         :category_list,
                        'channels'          :channels_dict,
                        'threads'           :threads,
                        'defalutChannelId'  :default_channel_id,
                        'debugMode'         :line_bot_table.debug_mode
                    })

                return JSONResponse(content=channels_json)