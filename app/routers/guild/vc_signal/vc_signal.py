from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from typing import List,Dict,Any,Tuple
from itertools import groupby,chain

from pkg.aio_req import aio_get_request
from pkg.oauth_check import discord_oauth_check,discord_get_profile
from pkg.permission import return_permission
from pkg.sort_channel import sort_channels
from model_types.discord_type.guild_permission import Permission
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser,Threads

from model_types.session_type import FastAPISession

from model_types.table_type import GuildVcChannel,GuildSetPermission
from model_types.environ_conf import EnvConf

from discord import Guild
from discord.ext import commands
from discord import ChannelType
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class VcSignalView(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guild/{guild_id}/vc-signal')
        async def vc_signal(
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
            TABLE = f'guilds_vc_signal'

            # サーバのチャンネル一覧を取得
            all_channel = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/guilds/{guild_id}/channels',
                headers={
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # チャンネルのソート
            all_channel_sort,all_channels,vc_channels = await sort_discord_vc_channel(all_channel=all_channel)

            vc_cate_sort = [
                tmp
                for tmp in all_channel_sort
                if tmp['type'] == 2 or tmp['type'] == 4
            ]

            text_channel_sort = [
                tmp
                for tmp in all_channel_sort
                if tmp['type'] == 0
            ]


            # サーバの情報を取得
            guild = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/guilds/{guild_id}',
                headers={
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # ログインユーザの情報を取得
            guild_user = await aio_get_request(
                url=f'{DISCORD_BASE_URL}/guilds/{guild_id}/members/{user_session.id}',
                headers={
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )
            role_list = [g for g in guild_user["roles"]]


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
                guild_permission_code = int(guild_table[0].get('vc_permission'))
                guild_permission_user = [
                    user
                    for user in guild_table[0].get('vc_user_id_permission')
                ]
                guild_permission_role = [
                    role
                    for role in guild_table[0].get('vc_role_id_permission')
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

            vc_set = []

            # ボイスチャンネルのみを代入
            app_vc = [int(x['id']) for x in vc_cate_sort if x['type'] == 2]

            # テータベース側のボイスチャンネルを代入
            db_vc = [int(x['vc_id']) for x in table_fetch]
            if set(app_vc) != set(db_vc):
                # データベース側で欠けているチャンネルを取得
                missing_items = [
                    item
                    for item in table_fetch
                    if item not in vc_cate_sort
                ]

                # 新しくボイスチャンネルが作成されていた場合
                if len(missing_items) > 0:
                    for vc in missing_items:
                        if vc['type'] == 2:
                            row_values = {
                                'vc_id': vc['id'],
                                'guild_id': guild_id,
                                'send_signal': True,
                                'send_channel_id': guild.get('system_channel_id'),
                                'join_bot': False,
                                'everyone_mention': True,
                                'mention_role_id':[]
                            }

                            # サーバー用に新たにカラムを作成
                            await DB.insert_row(
                                table_name=TABLE,
                                row_values=row_values
                            )
                            vc_set.append(row_values)
                # ボイスチャンネルがいくつか削除されていた場合
                else:
                    # 削除されたチャンネルを取得
                    missing_items = [
                        item
                        for item in all_channels
                        if item not in table_fetch
                    ]

                    # 削除されたチャンネルをテーブルから削除
                    for vc in missing_items:
                        await DB.delete_row(
                            table_name=TABLE,
                            where_clause={
                                'vc_id':vc['vc_id']
                            }
                        )

                    # 削除後のチャンネルを除き、残りのチャンネルを取得
                    vc_set = [
                        d for d in table_fetch
                        if not (d.get('vc_id') in [
                            e.get('vc_id') for e in missing_items
                        ] )
                    ]

            else:
                vc_set = table_fetch

                # データベースの状況を取得
                db_check_fetch = await DB.select_rows(
                    table_name=TABLE,
                    columns=[],
                    where_clause={
                        'guild_id':guild_id
                    }
                )
                # データベースに登録されたが、削除されずに残っているチャンネルを削除
                check = [int(c['vc_id']) for c in db_check_fetch]
                del_check = set(check) - set(app_vc)

                for chan_id in list(del_check):
                    await DB.delete_row(
                        table_name=TABLE,
                        where_clause={
                            'channel_id':chan_id
                        }
                    )

            return templates.TemplateResponse(
                "guild/vc_signal/vc_signal.html",
                {
                    "request": request,
                    "vc_cate_channel": vc_cate_sort,
                    "text_channel": text_channel_sort,
                    "guild": guild,
                    "guild_id": guild_id,
                    'vc_set' : vc_set,
                    "user_permission":user_permission,
                    "title": "ボイスチャンネルの送信設定/" + guild['name']
                }
            )

        @self.router.get('/guild/{guild_id}/vc-signal/view')
        async def vc_signal(
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
                    TABLE = f'guilds_vc_signal'

                    db_vc_channels:List[Dict] = await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':guild_id
                        }
                    )

                    # システムチャンネルがある場合代入
                    if hasattr(guild.system_channel,'id'):
                        system_channel_id = guild.system_channel.id
                    else:
                        system_channel_id = 0

                    # データベース内のボイスチャンネルの一覧
                    vc_db_list_id = [
                        int(cc.get('vc_id'))
                        for cc in db_vc_channels
                    ]

                    # ボイスチャンネルのid一覧
                    vc_id_list = [
                        g.id
                        for g in guild.channels
                        if g.type == ChannelType.voice
                    ]

                    # 新しくチャンネルが作成された場合
                    if set(vc_db_list_id) != set(vc_id_list):
                        # 新しく作られたチャンネルを抜き出す
                        missing_channels = [
                            item
                            for item in vc_id_list
                            if item not in vc_db_list_id
                        ]

                        # デフォルトで作成
                        for channel_id in missing_channels:
                            await DB.insert_row(
                                table_name=TABLE,
                                row_values={
                                    'vc_id'             :channel_id,
                                    'guild_id'          :guild.id,
                                    'send_signal'       :True,
                                    'send_channel_id'   :system_channel_id,
                                    'join_bot'          :True,
                                    'everyone_mention'  :True,
                                    'mention_role_id'   :[]
                                }
                            )

                        # 新規作成がない場合、削除されたチャンネルを抜き出す
                        if len(missing_channels) == 0:
                            missing_channels = [
                                item
                                for item in vc_db_list_id
                                if item not in vc_id_list
                            ]
                            # データベースから削除
                            for channel_id in missing_channels:
                                await DB.delete_row(
                                    table_name=TABLE,
                                    where_clause={
                                        'channel_id':channel_id
                                    }
                                )

                        db_vc_channels:List[Dict] = await DB.select_rows(
                            table_name=TABLE,
                            columns=[],
                            where_clause={
                                'guild_id':guild_id
                            }
                        )

                    db_vc_channels:List[GuildVcChannel] = [
                        GuildVcChannel(**b)
                        for b in db_vc_channels
                    ]

                    # カテゴリーごとにチャンネルをソート
                    category_dict,category_index = await sort_channels(channels=guild.channels)

                    channels_json = dict()
                    channels_dict = dict()
                    vc_channel_dict = dict()

                    channels_list = list()
                    category_list = list()
                    vc_channel_list = list()
                    vc_list = list()

                    for category_id,category_value in category_index.items():
                        index_list = [
                            list(map(
                                lambda x:int(x.vc_id),
                                db_vc_channels
                            )).index(index.id)
                            for index in category_dict.get(category_id)
                            if index.type == ChannelType.voice
                        ]
                        vc_list = [
                            vc
                            for vc in category_dict.get(category_id)
                            if vc.type == ChannelType.voice
                        ]
                        vc_channel_list = [
                            {
                                'id'                :str(chan.id),
                                'name'              :chan.name,
                                'sendSignal'        :db_vc_channels[i].send_signal,
                                'sendChannelId'     :str(db_vc_channels[i].send_channel_id),
                                'joinBot'           :db_vc_channels[i].join_bot,
                                'everyoneMention'   :db_vc_channels[i].everyone_mention,
                                'mentionRoleId'     :[
                                    str(role_id)
                                    for role_id in db_vc_channels[i].mention_role_id
                                ]
                            }
                            for chan,i in zip(vc_list,index_list)
                        ]

                        vc_channel_dict.update({
                            category_id:vc_channel_list
                        })

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
                                'type'  :type(chan).__name__,
                            }
                            for chan in category_dict.get(category_id)
                        ]
                        channels_dict.update({
                            category_id:channels_list
                        })


                    index_list = [
                        list(map(
                            lambda x:int(x.vc_id),
                            db_vc_channels
                        )).index(index.id)
                        for index in category_dict.get('None')
                        if index.type == ChannelType.voice
                    ]

                    vc_list = [
                        vc
                        for vc in category_dict.get(category_id)
                        if vc.type == ChannelType.voice
                    ]

                    # カテゴリーなしのチャンネル一覧
                    vc_channel_dict.update({
                        'None':[
                            {
                                'id'                :str(none_channel.id),
                                'name'              :none_channel.name,
                                'sendSignal'        :db_vc_channels[i].send_signal,
                                'sendChannelId'     :str(db_vc_channels[i].send_channel_id),
                                'joinBot'           :db_vc_channels[i].join_bot,
                                'everyoneMention'   :db_vc_channels[i].everyone_mention,
                                'mentionRoleId'     :[
                                    str(role_id)
                                    for role_id in db_vc_channels[i].mention_role_id
                                ]
                            }
                            for none_channel,i in zip(vc_list,index_list)
                        ]
                    })

                    # カテゴリーなしのチャンネル一覧
                    channels_dict.update({
                        'None':[
                            {
                                'id'    :str(none_channel.id),
                                'name'  :none_channel.name,
                                'type'  :type(none_channel).__name__,
                            }
                            for none_channel in category_dict.get('None')
                        ]
                    })

                    # スレッド一覧
                    threads = [
                        {
                            'id'    :str(thread.id),
                            'name'  :thread.name,
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
                                'name'  :thread.name,
                            }
                            for thread in arc_threads
                        ]

                        threads.extend(archived_threads)

                    # サーバー内のメンバー一覧
                    guild_users = [
                        {
                            'id'                :str(user.id),
                            'name'              :user.name,
                            'userDisplayName'   :user.display_name
                        }
                        for user in guild.members
                    ]

                    # サーバー内でのロール一覧
                    guild_roles = [
                        {
                            'id'    :str(user.id),
                            'name'  :user.name
                        }
                        for user in guild.roles
                    ]

                    channels_json.update({
                        'guildIcon'         :guild._icon,
                        'guildName'         :guild.name,
                        'categorys'         :category_list,
                        'channels'          :channels_dict,
                        'vcChannels'        :vc_channel_dict,
                        'threads'           :threads,
                        'users'             :guild_users,
                        'roles'             :guild_roles,
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
    and_code = guild_line_permission.vc_permission & permission_code
    admin_code = 8 & permission_code

    # ユーザが持っているロールid一覧を取得
    guild_user_data = guild.get_member(user_id)
    guild_user_roles = [
        role.id
        for role in guild_user_data.roles
    ]

    # 許可されている場合、管理者の場合
    if (and_code == permission_code or
        admin_code == 8 or
        user_id in guild_line_permission.vc_user_id_permission or
        len(set(guild_line_permission.vc_role_id_permission) & set(guild_user_roles)) > 0
        ):
        # 変更可能
        return True
    else:
        # 変更不可
        return False

async def sort_discord_vc_channel(
    all_channel:List
) -> Tuple[List,List,List]:
    # 親カテゴリー格納用
    position = []
    # ソート後のチャンネル一覧
    all_channel_sort = []

    # レスポンスのJSONからpositionでソートされたリストを作成
    sorted_channels = sorted(all_channel, key=lambda c: c['position'])

    # parent_idごとにチャンネルをまとめた辞書を作成
    channel_dict = {}

    for parent_id, group in groupby(
        sorted_channels,
        key=lambda c: c['parent_id']
    ):
        if parent_id is None:
            # 親カテゴリーのないチャンネルは、キーがNoneの辞書に追加される
            parent_id = 'None'

        # キーがまだない場合、作成(同時に値も代入)
        if channel_dict.get(str(parent_id)) == None:
            channel_dict[str(parent_id)] = list(group)
        # キーがある場合、リストを取り出して結合し代入
        else:
            listtmp:List = channel_dict[str(parent_id)]
            listtmp.extend(list(group))

            # リスト内包記法でボイスチャンネルとカテゴリー以外は除外
            listtmp = [
                tmp
                for tmp in listtmp
            ]
            channel_dict[str(parent_id)] = listtmp
            # リストを空にする
            listtmp = list()

    # 親カテゴリーがある場合、Noneから取り出す
    for chan in channel_dict['None'][:]:
        if chan['type'] == 4:
            position.append(chan)
            channel_dict['None'].remove(chan)

    # 辞書を表示
    position_index = 0

    # 親カテゴリーの名前をリスト化
    extracted_list = [d["name"] for d in position]
    # カテゴリーに属しないチャンネルが存在する場合
    if len(channel_dict['None']) != 0:
        # 配列の長さをカテゴリー数+1にする
        all_channels = [{}] * (len(extracted_list) + 1)
        vc_channels = [{}] * (len(extracted_list) + 1)
    else:
        all_channels = [{}] * len(extracted_list)
        vc_channels = [{}] * len(extracted_list)

    for parent_id, channel in channel_dict.items():
        # カテゴリー内にチャンネルがある場合
        if len(channel) != 0:
            for d in position:
                # カテゴリーを探索、あった場合positionを代入
                if d['id'] == channel[0]['parent_id']:
                    position_index = d['position']
                    break
        else:
            position_index = len(extracted_list)

        if len(channel) != 0:
            # 指定したリストの中身が空でない場合、空のリストを探す
            while len(all_channels[position_index]) != 0:
                if len(extracted_list) == position_index:
                    position_index -= 1
                else:
                    position_index += 1

            # 指定した位置にカテゴリー内のチャンネルを代入
            all_channels[position_index] = channel
            vc_channels[position_index] = channel

            # 先頭がカテゴリーでない場合
            if channel[0]['parent_id'] != None:
                # 先頭にカテゴリーチャンネルを代入
                all_channels[position_index].insert(0,d)

    # list(list),[[],[]]を一つのリストにする
    all_channel_sort = list(chain.from_iterable(all_channels))

    return all_channel_sort,all_channels,vc_channels