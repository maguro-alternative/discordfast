from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict,Any,Union

from base.aio_req import (
    aio_get_request,
    return_permission,
    discord_oauth_check
    get_profile,
    sort_discord_channel,
    sort_channels
)
from model_types.discord_type.guild_permission import Permission
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser

from model_types.session_type import FastAPISession

from model_types.table_type import GuildLineChannel,GuildSetPermission

from discord.channel import (
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
)
from discord import Guild
from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import DB

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

GuildChannel = Union[
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class LinePostView(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guild/{guild_id}/line-post')
        async def line_post(
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
            TABLE = f'guilds_line_channel_{guild_id}'

            # サーバのチャンネル一覧を取得
            all_channel = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            limit = os.environ.get('USER_LIMIT',default=100)

            # サーバのメンバー一覧を取得
            guild_members = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members?limit={limit}',
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

            role_list = [
                g
                for g in guild_user["roles"]
            ]

            # サーバの権限を取得
            guild_user_permission = await return_permission(
                guild_id=guild_id,
                user_id=user_session.id,
                access_token=oauth_session.access_token
            )

            # パーミッションの番号を取得
            permission_code = await guild_user_permission.get_permission_code()

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
                guild_permission_code = int(guild_table[0].get('line_permission'))
                guild_permission_user = [
                    user
                    for user in guild_table[0].get('line_user_id_permission')
                ]
                guild_permission_role = [
                    role
                    for role in guild_table[0].get('line_role_id_permission')
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
                channel_id:int = table.get('channel_id')
                line_ng_channel:bool = table.get('line_ng_channel')
                ng_message_type:List[str] = table.get('ng_message_type')
                message_bot:bool = table.get('message_bot')
                ng_users:List[int] = table.get('ng_users')

                line_row.update(
                    {
                        str(channel_id):{
                            'line_ng_channel':line_ng_channel,
                            'ng_message_type':ng_message_type,
                            'message_bot':message_bot,
                            'ng_users':ng_users
                        }
                    }
                )

            # ローカルに保存されているチャンネルの数
            table_ids = [
                int(tid["channel_id"])
                for tid in table_fetch
            ]
            # Discord側の現時点でのチャンネルの数(カテゴリーチャンネルを除く)
            guild_ids = [
                int(aid["id"])
                for aid in all_channel_sort
                if aid['type'] != 4
            ]
            # 新規で作られたチャンネルを取得
            new_channel = [
                c
                for c in all_channel_sort
                if int(c['id']) not in table_ids and c['type'] != 4
            ]
            # 消されたチャンネルを取得
            del_channel = set(table_ids) - set(guild_ids)

            # チャンネルの新規作成、削除があった場合
            if len(new_channel) > 0 or len(del_channel) > 0:
                # データベースへ接続
                if DB.conn == None:
                    await DB.connect()
                new_values = []
                # 新規作成された場合
                if len(new_channel) > 0:
                    for new in new_channel:
                        if new['id'] not in table_ids:
                            new_row = {
                                'channel_id': new['id'],
                                'guild_id':guild_id,
                                'line_ng_channel':False,
                                'ng_message_type':[],
                                'message_bot':False,
                                'ng_users':[]
                            }
                            new_values.append(new_row)

                        line_row.update(
                            {
                                str(new['id']):{
                                    'line_ng_channel':False,
                                    'ng_message_type':[],
                                    'message_bot':False,
                                    'ng_users':[]
                                }
                            }
                        )

                    # バッジで一気に作成
                    await DB.batch_insert_row(
                        table_name=TABLE,
                        row_values=new_values
                    )

                # 削除された場合
                if len(del_channel) > 0:
                    for chan_id in list(del_channel):
                        await DB.delete_row(
                            table_name=TABLE,
                            where_clause={
                                'channel_id':chan_id
                            }
                        )

                # データベースの状況を取得
                db_check_fetch = await DB.select_rows(
                    table_name=TABLE,
                    columns=[],
                    where_clause={}
                )

                # データベースに登録されたが、削除されずに残っているチャンネルを削除
                check = [int(c['channel_id']) for c in db_check_fetch]
                del_check = set(check) - set(guild_ids)

                for chan_id in list(del_check):
                    await DB.delete_row(
                        table_name=TABLE,
                        where_clause={
                            'channel_id':chan_id
                        }
                    )

            return templates.TemplateResponse(
                "guild/line/linepost.html",
                {
                    "request": request,
                    "guild": guild,
                    "guild_id": guild_id,
                    "guild_members":guild_members,
                    "all_channel": all_channel_sort,
                    "line_row":line_row,
                    "user_permission":user_permission,
                    "title": "LINEへの送信設定/" + guild["name"]
                }
            )

        @self.router.get('/guild/{guild_id}/line-post/view')
        async def line_post(
            guild_id:int,
            request:Request
        ) -> JSONResponse:
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token = session.discord_oauth_data.access_token
                # Discordのユーザ情報を取得
                discord_user = await get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            for guild in self.bot.guilds:
                if guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE == False:
                        # サーバの権限を取得
                        permission = await return_permission(
                            guild_id=guild.id,
                            user_id=discord_user.id,
                            access_token=access_token
                        )

                        # 編集可能かどうか
                        chenge_permission = await chenge_permission_check(
                            user_id=discord_user.id,
                            permission=permission,
                            guild=guild
                        )
                    else:
                        chenge_permission = False

                    # 使用するデータベースのテーブル名
                    TABLE = f'guilds_line_channel_{guild.id}'

                    db_channels:List[Dict] = await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={}
                    )

                    # データベース内のチャンネルとスレッドの一覧
                    guild_db_list_id = [
                        int(cc.get('channel_id'))
                        for cc in db_channels
                    ]

                    # チャンネルとスレッドのid一覧
                    guild_id_list = [
                        g.id
                        for g in guild.channels
                    ]
                    for thread in guild.threads:
                        guild_id_list.append(thread.id)

                    # 新しくチャンネルが作成された場合
                    if set(guild_db_list_id) != set(guild_id_list):
                        # 新しく作られたチャンネルを抜き出す
                        missing_channels = [
                            item
                            for item in guild_id_list
                            if item not in guild_db_list_id
                        ]
                        # デフォルトで作成
                        for channel_id in missing_channels:
                            await DB.insert_row(
                                table_name=TABLE,
                                row_values={
                                    'channel_id'        :channel_id,
                                    'guild_id'          :guild.id,
                                    'line_ng_channel'   :False,
                                    'ng_message_type'   :[],
                                    'message_bot'       :True,
                                    'ng_users'          :[]
                                }
                            )
                        # 新規作成がない場合、削除されたチャンネルを抜き出す
                        if len(missing_channels) == 0:
                            missing_channels = [
                                item
                                for item in guild_db_list_id
                                if item not in guild_id_list
                            ]
                            # データベースから削除
                            for channel_id in missing_channels:
                                await DB.delete_row(
                                    table_name=TABLE,
                                    where_clause={
                                        'channel_id':channel_id
                                    }
                                )

                        db_channels:List[Dict] = await DB.select_rows(
                            table_name=TABLE,
                            columns=[],
                            where_clause={}
                        )

                    db_channels:List[GuildLineChannel] = [
                        GuildLineChannel(**b)
                        for b in db_channels
                    ]

                    # カテゴリーごとにチャンネルをソート
                    category_dict,category_index = await sort_channels(channels=guild.channels)

                    channels_json = dict()
                    channels_dict = dict()

                    channels_list = list()
                    category_list = list()

                    for category_id,category_value in category_index.items():
                        # ソートしたチャンネルと同じ順番にするため配列番号一覧を格納
                        index_list = [
                            list(map(
                                lambda x:int(x.channel_id),
                                db_channels
                            )).index(index.id)
                            for index in category_dict.get(category_id)
                        ]
                        # カテゴリーチャンネル一覧
                        category_list.append({
                            'id'    :str(category_value.id),
                            'name'  :category_value.name
                        })
                        # カテゴリー内のチャンネル一覧
                        channels_list = [
                            {
                                'id'            :str(chan.id),
                                'name'          :chan.name,
                                'type'          :type(chan).__name__,
                                'lineNgChannel' :db_channels[i].line_ng_channel,
                                'ngMessageType' :db_channels[i].ng_message_type,
                                'messageBot'    :db_channels[i].message_bot,
                                'ngUsers'       :db_channels[i].ng_users
                            }
                            for chan,i in zip(category_dict.get(category_id),index_list)
                        ]
                        channels_dict.update({
                            category_id:channels_list
                        })


                    # ソートしたチャンネルと同じ順番にするため配列番号一覧を格納
                    index_list = [
                        list(map(
                            lambda x:int(x.channel_id),
                            db_channels
                        )).index(index.id)
                        for index in category_dict.get('None')
                    ]

                    # カテゴリーなしのチャンネル一覧
                    channels_dict.update({
                        'None':[
                            {
                                'id'            :str(none_channel.id),
                                'name'          :none_channel.name,
                                'type'          :type(none_channel).__name__,
                                'lineNgChannel' :db_channels[i].line_ng_channel,
                                'ngMessageType' :db_channels[i].ng_message_type,
                                'messageBot'    :db_channels[i].message_bot,
                                'ngUsers'       :db_channels[i].ng_users
                            }
                            for none_channel,i in zip(category_dict.get('None'),index_list)
                        ]
                    })

                    # ソートしたチャンネルと同じ順番にするため配列番号一覧を格納
                    index_list = [
                        list(map(
                            lambda x:int(x.channel_id),
                            db_channels
                        )).index(index.id)
                        for index in guild.threads
                    ]

                    # スレッド一覧
                    threads = [
                        {
                            'id'            :str(thread.id),
                            'name'          :thread.name,
                            'lineNgChannel' :db_channels[i].line_ng_channel,
                            'ngMessageType' :db_channels[i].ng_message_type,
                            'messageBot'    :db_channels[i].message_bot,
                            'ngUsers'       :db_channels[i].ng_users
                        }
                        for thread,i in zip(guild.threads,index_list)
                    ]

                    # サーバー内のメンバー一覧
                    guild_users = [
                        {
                            'id'                :str(user.id),
                            'name'              :user.name,
                            'userDisplayName'   :user.display_name
                        }
                        for user in guild.members
                    ]

                    channels_json.update({
                        'categorys'         :category_list,
                        'channels'          :channels_dict,
                        'threads'           :threads,
                        'users'             :guild_users,
                        'chengePermission'  :chenge_permission
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
    and_code = guild_line_permission.line_permission & permission_code
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
        user_id in guild_line_permission.line_user_id_permission or
        len(set(guild_line_permission.line_role_id_permission) & set(guild_user_roles)) > 0
        ):
        # 変更可能
        return True
    else:
        # 変更不可
        return False