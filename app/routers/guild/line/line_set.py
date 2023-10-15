from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from typing import List,Dict,Any

from pkg.aio_req import aio_get_request
from pkg.oauth_check import discord_oauth_check,discord_get_profile
from pkg.permission import return_permission
from pkg.sort_channel import sort_channels,sort_discord_channel
from pkg.crypt import decrypt_password
from model_types.discord_type.guild_permission import Permission
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser,Threads

from model_types.session_type import FastAPISession

from model_types.table_type import LineBotColunm,GuildSetPermission
from model_types.environ_conf import EnvConf

from discord import Guild,ChannelType
from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN
ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class LineSetView(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guild/{guild_id}/line-set')
        async def line_set(
            request:Request,
            guild_id:int
        ):
            # OAuth2トークンが有効かどうか判断
            if request.session.get('discord_oauth_data'):
                oauth_session = DiscordOAuthData(**request.session.get('discord_oauth_data'))
                user_session = DiscordUser(**request.session.get('discord_user'))
                # トークンの有効期限が切れていた場合、再ログインする
                if not await discord_oauth_check(access_token=oauth_session.access_token):
                    return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            else:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)

            # 使用するデータベースのテーブル名
            TABLE = f'line_bot'

            # サーバのチャンネル一覧を取得
            all_channel = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # ソート後のチャンネル一覧
            all_channel_sort = await sort_discord_channel(all_channel=all_channel)

            # サーバの情報を取得
            guild = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # ログインユーザの情報を取得
            guild_user = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{user_session.id}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

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
                a_thead.update({'type':15})
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
                    a_thead.update({'type':15})
                    all_channel_sort.append(a_thead)

            role_list = [
                g
                for g in guild_user["roles"]
            ]

            # サーバの権限を取得
            guild_user_permission = await return_permission(
                user_id=user_session.id,
                guild=[
                    guild
                    for guild in self.bot.guilds
                    if guild.id == guild_id
                ][0]
            )

            # パーミッションの番号を取得
            permission_code = await guild_user_permission.get_permission_code()

            if DB.conn == None:
                await DB.connect()

            guild_table:List[Dict[str,Any]] = await DB.select_rows(
                table_name='guild_set_permissions',
                columns=[],
                where_clause={
                    'guild_id':guild_id
                }
            )

            guild_permission_code = 8
            guild_permission_user = list()
            guild_permission_role = list()
            if len(guild_table) > 0:
                guild_permission_code = int(guild_table[0].get('line_bot_permission'))
                guild_permission_user = [
                    user
                    for user in guild_table[0].get('line_bot_user_id_permission')
                ]
                guild_permission_role = [
                    role
                    for role in guild_table[0].get('line_bot_role_id_permission')
                ]

            and_code = guild_permission_code & permission_code
            admin_code = 8 & permission_code
            user_permission:str = 'normal'

            # 許可されている場合、管理者の場合
            if (and_code == permission_code or
                admin_code == 8 or
                user_session.id in guild_permission_user or
                len(set(guild_permission_role) & set(role_list)) > 0
                ):
                user_permission = 'admin'

            table_fetch:List[Dict[str,Any]] = await DB.select_rows(
                table_name=TABLE,
                columns=[],
                where_clause={
                    'guild_id':guild_id
                }
            )

            line_row = {}

            # 各項目をフロント部分に渡す
            for table in table_fetch:
                if int(table.get('guild_id')) == guild_id:
                    line_notify_token:str = await decrypt_password(encrypted_password=bytes(table.get('line_notify_token')))
                    line_bot_token:str = await decrypt_password(encrypted_password=bytes(table.get('line_bot_token')))
                    line_bot_secret:str = await decrypt_password(encrypted_password=bytes(table.get('line_bot_secret')))
                    line_group_id:str = await decrypt_password(encrypted_password=bytes(table.get('line_group_id')))
                    line_client_id:str = await decrypt_password(encrypted_password=bytes(table.get('line_client_id')))
                    line_client_secret:str = await decrypt_password(encrypted_password=bytes(table.get('line_client_secret')))
                    default_channel_id:int = int(table.get('default_channel_id'))
                    debug_mode:bool = bool(table.get('debug_mode'))

                    line_row = {
                        'line_notify_token':line_notify_token,
                        'line_bot_token':line_bot_token,
                        'line_bot_secret':line_bot_secret,
                        'line_group_id':line_group_id,
                        'line_client_id':line_client_id,
                        'line_client_secret':line_client_secret,
                        'default_channel_id':default_channel_id,
                        'debug_mode':debug_mode
                    }


            return templates.TemplateResponse(
                "guild/line/lineset.html",
                {
                    "request": request,
                    "guild": guild,
                    "guild_id": guild_id,
                    "all_channel": all_channel_sort,
                    "line_row":line_row,
                    "user_permission":user_permission,
                    "title": "LINEBOTおよびグループ設定/" + guild['name']
                }
            )

        @self.router.get('/guild/{guild_id}/line-set/view')
        async def line_post(
            guild_id:int,
            request:Request
        ):
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token = session.discord_oauth_data.access_token
                # Discordのユーザ情報を取得
                discord_user = await discord_get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            for guild in self.bot.guilds:
                if guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE:
                        chenge_permission = False
                    else:
                        # サーバの権限を取得
                        permission = await return_permission(
                            user_id=discord_user.id,
                            guild=guild
                        )

                        # 編集可能かどうか
                        chenge_permission = await chenge_permission_check(
                            user_id=discord_user.id,
                            permission=permission,
                            guild=guild
                        )
                    # 使用するデータベースのテーブル名
                    TABLE = f'line_bot'

                    db_line_bot:List[Dict] = await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':guild.id
                        }
                    )

                    line_bot = LineBotColunm(**db_line_bot[0])

                    line_notify_token:str = await decrypt_password(encrypted_password=line_bot.line_notify_token)
                    line_bot_token:str = await decrypt_password(encrypted_password=line_bot.line_bot_token)
                    line_bot_secret:str = await decrypt_password(encrypted_password=line_bot.line_bot_secret)
                    line_group_id:str = await decrypt_password(encrypted_password=line_bot.line_group_id)
                    line_client_id:str = await decrypt_password(encrypted_password=line_bot.line_client_id)
                    line_client_secret:str = await decrypt_password(encrypted_password=line_bot.line_client_secret)

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

                    # フロント側に送るjsonを作成(linebotの情報は先頭3桁のみ)
                    channels_json.update({
                        'guildIcon'         :guild._icon,
                        'guildName'         :guild.name,
                        'categorys'         :category_list,
                        'channels'          :channels_dict,
                        'threads'           :threads,
                        'chengePermission'  :chenge_permission,
                        'lineNotifyToken'   :line_notify_token[:3],
                        'lineBotToken'      :line_bot_token[:3],
                        'lineBotSecret'     :line_bot_secret[:3],
                        'lineGroupId'       :line_group_id[:3],
                        'lineClientId'      :line_client_id[:3],
                        'lineClientSecret'  :line_client_secret[:3],
                        'defalutChannelId'  :str(line_bot.default_channel_id),
                        'debugMode'         :line_bot.debug_mode
                    })

                    return JSONResponse(content=channels_json)



async def chenge_permission_check(
    user_id:int,
    permission:Permission,
    guild:Guild
) -> bool:
    """
    ログインユーザが編集可能かどうか識別

    Args:
        user_id (int):
            DiscordUserのid
        permission (Permission):
            ユーザの権限
        guild (Guild):
            サーバ情報

    Returns:
        bool: 編集可能かどうか
    """
    # パーミッションの番号を取得
    permission_code = await permission.get_permission_code()

    # アクセス権限の設定を取得
    guild_p:List[Dict] = await DB.select_rows(
        table_name='guild_set_permissions',
        columns=[],
        where_clause={
            'guild_id':guild.id
        }
    )
    guild_line_permission = GuildSetPermission(**guild_p[0])

    # 指定された権限を持っているか、管理者権限を持っているか
    and_code = guild_line_permission.line_bot_permission & permission_code
    admin_code = 8 & permission_code

    # ロールid一覧を取得
    guild_user_data = guild.get_member(user_id)
    guild_user_roles = [
        role.id
        for role in guild_user_data.roles
    ]

    # 許可されている場合、管理者の場合
    if (and_code == permission_code or
        admin_code == 8 or
        user_id in guild_line_permission.line_bot_user_id_permission or
        len(set(guild_line_permission.line_bot_role_id_permission) & set(guild_user_roles)) > 0
        ):
        # 変更可能
        return True
    else:
        # 変更不可
        return False