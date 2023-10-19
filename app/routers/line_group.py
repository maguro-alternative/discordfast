from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from typing import List,Dict

from pkg.aio_req import aio_get_request
from pkg.sort_channel import sort_channels,sort_discord_channel
from pkg.crypt import decrypt_password

from model_types.session_type import FastAPISession
from model_types.line_type.line_oauth import LineTokenVerify,LineProfile
from model_types.table_type import LineBotColunm
from model_types.discord_type.discord_type import Threads
from model_types.environ_conf import EnvConf

from discord import ChannelType
from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

LINE_OAUTH_BASE_URL = EnvConf.LINE_OAUTH_BASE_URL
LINE_BOT_URL = EnvConf.LINE_BOT_URL

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

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
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # OAuth2トークンが有効かどうか判断
            if session.line_oauth_data:
                try:
                    oauth_session = await aio_get_request(
                        url=f"{LINE_OAUTH_BASE_URL}/verify?access_token={session.line_oauth_data.access_token}",
                        headers={}
                    )
                    # トークンの有効期限が切れていた場合、再ログインする
                    if oauth_session.get('error_description') == 'Invalid IdToken Nonce.':
                        return RedirectResponse(url='/line-login')
                except KeyError:
                    return RedirectResponse(url='/line-login')
            else:
                return RedirectResponse(url='/line-login')

            # line_botテーブルの読み込み
            line_bot_table:List[Dict] = await DB.select_rows(
                table_name='line_bot',
                columns=[],
                where_clause={
                    'guild_id':int(guild_id)
                }
            )

            guild_set_line_bot = LineBotColunm(**line_bot_table[0])

            # 復号化
            line_group_id:str = await decrypt_password(encrypted_password=guild_set_line_bot.line_group_id)
            line_bot_token:str = await decrypt_password(encrypted_password=guild_set_line_bot.line_bot_token)

            # LINE→Discordへの送信先チャンネルid
            default_channel_id:int = guild_set_line_bot.default_channel_id

            # グループIDが有効かどうか判断
            r = await aio_get_request(
                url=f"{LINE_BOT_URL}/group/{line_group_id}/member/{session.line_user.sub}",
                headers={
                    'Authorization': f'Bearer {line_bot_token}'
                }
            )
            # グループIDが無効の場合、友達から判断
            if r.get('message') != None:
                raise HTTPException(status_code=400, detail="認証失敗")

            # サーバのチャンネル一覧を取得
            all_channel = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/guilds/{guild_id}/channels',
                headers={
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # ソート後のチャンネル一覧
            all_channel_sort = await sort_discord_channel(all_channel=all_channel)

            # アクティブスレッドを取得
            active_threads = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/guilds/{guild_id}/threads/active',
                headers={
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
                    url=f'{DISCORD_BASE_URL}/channels/{thread_id}/threads/archived/public',
                    headers={
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

        @self.router.get('/group/{guild_id}/line-group/view')
        async def group(
            request:Request,
            guild_id:int
        ):
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE:
                line_user = {
                    'scope'     :'profile%20openid%20email',
                    'client_id' :'0',
                    'expires_in':100
                }
            else:
                # アクセストークンの復号化
                access_token:str = session.line_oauth_data.access_token
                user_sub:str = session.line_user.sub
                # LINEのユーザ情報を取得
                line_user = await aio_get_request(
                    url=f"{LINE_OAUTH_BASE_URL}/verify?access_token={access_token}",
                    headers={}
                )
                line_user = LineTokenVerify(**line_user)

                # トークンが無効
                if line_user.error != None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            TABLE = 'line_bot'

            for guild in self.bot.guilds:
                if guild_id == guild.id:
                    l = await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':guild_id
                        }
                    )

                    line_bot_table = LineBotColunm(**l[0])

                    # 復号化
                    line_group_id:str = await decrypt_password(encrypted_password=bytes(line_bot_table.line_group_id))
                    line_bot_token:str = await decrypt_password(encrypted_password=bytes(line_bot_table.line_bot_token))

                    # LINE→Discordへの送信先チャンネルid
                    default_channel_id = line_bot_table.default_channel_id

                    # デバッグモード
                    if DEBUG_MODE:
                        r = {
                            'displayName'   :'test',
                            'userId'        :'aaa',
                            'pictureUrl'    :'png'
                        }
                        line_group_profile = LineProfile(**r)
                    else:
                        # グループIDが有効かどうか判断
                        r = await aio_get_request(
                            url=f"{LINE_BOT_URL}/group/{line_group_id}/member/{user_sub}",
                            headers={
                                'Authorization': f'Bearer {line_bot_token}'
                            }
                        )
                        line_group_profile = LineProfile(**r)
                        # グループIDが無効の場合、友達から判断
                        if line_group_profile.message != None:
                            raise HTTPException(status_code=400, detail="認証失敗")

                    # カテゴリーごとにチャンネルをソート
                    category_dict,category_index = await sort_channels(channels=guild.channels)

                    channels_json = dict()
                    channels_dict = dict()

                    channels_list = list()
                    category_list = list()

                    for category_id,category_value in category_index.items():
                        # カテゴリーチャンネル一覧
                        category_list.append({
                            'id'    :str(category_value.id),
                            'name'  :category_value.name
                        })
                        # カテゴリー内のチャンネル一覧
                        channels_list = [
                            {
                                'id'    :str(chan.id),
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
                                'id'    :str(chan.id),
                                'name'  :chan.name,
                                'type'  :type(chan).__name__
                            }
                            for chan in category_dict.get('None')
                        ]
                    })

                    # スレッド一覧
                    threads = [
                        {
                            'id'    :str(thread.id),
                            'name'  :thread.name
                        }
                        for thread in guild.threads
                    ]

                    forum_channels = [
                        f
                        for f in guild.channels
                        if f.type == ChannelType.forum
                    ]

                    for forum_channel in forum_channels:
                        # アーカイブスレッドを取得
                        arc_threads = await aio_get_request(
                            url=f'{DISCORD_BASE_URL}/channels/{forum_channel.id}/threads/archived/public',
                            headers={
                                'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                            }
                        )

                        arc_threads = [
                            Threads(**t)
                            for t in arc_threads.get('threads')
                        ]

                        archived_threads = [
                            {
                                'id'    :str(thread.id),
                                'name'  :thread.name
                            }
                            for thread in arc_threads
                        ]

                        threads.extend(archived_threads)

                    channels_json.update({
                        'categorys'         :category_list,
                        'channels'          :channels_dict,
                        'threads'           :threads,
                        'defalutChannelId'  :str(default_channel_id),
                        'debugMode'         :line_bot_table.debug_mode
                    })

                return JSONResponse(content=channels_json)