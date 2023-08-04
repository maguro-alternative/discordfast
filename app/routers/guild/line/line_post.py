from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
from typing import List,Dict,Any,Union,Tuple

from base.database import PostgresDB
from base.aio_req import (
    aio_get_request,
    pickle_read,
    return_permission,
    oauth_check,
    get_profile,
    sort_discord_channel,
    decrypt_password
)
from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser,DiscordChannel
from model_types.discord_type.discord_request_type import DiscordBaseRequest

from model_types.table_type import GuildLineChannel

from discord.channel import (
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
)

import pprint

from discord import ChannelType
from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

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
                if not await oauth_check(access_token=oauth_session.access_token):
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

            # キャッシュ読み取り
            guild_table_fetch:List[Dict[str,Any]] = await pickle_read(filename='guild_set_permissions')

            guild_table = [
                g
                for g in guild_table_fetch
                if int(g.get('guild_id')) == guild_id
            ]
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

            # キャッシュ読み取り
            table_fetch:List[Dict[str,Any]] = await pickle_read(filename=TABLE)

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
                await db.connect()
                new_values = []
                # 新規作成された場合
                if len(new_channel) > 0:
                    for new in new_channel:
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
                    await db.batch_insert_row(
                        table_name=TABLE,
                        row_values=new_values
                    )

                # 削除された場合
                if len(del_channel) > 0:
                    for chan_id in list(del_channel):
                        await db.delete_row(
                            table_name=TABLE,
                            where_clause={
                                'channel_id':chan_id
                            }
                        )

                # データベースの状況を取得
                db_check_fetch = await db.select_rows(
                    table_name=TABLE,
                    columns=[],
                    where_clause={}
                )

                # データベースに登録されたが、削除されずに残っているチャンネルを削除
                check = [int(c['channel_id']) for c in db_check_fetch]
                del_check = set(check) - set(guild_ids)

                for chan_id in list(del_check):
                    await db.delete_row(
                        table_name=TABLE,
                        where_clause={
                            'channel_id':chan_id
                        }
                    )

                await db.disconnect()


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

        @self.router.post('/guild/line-post')
        async def line_post(
            request:DiscordBaseRequest
            #request:Request
        ):
            if db.conn != None:
                await db.connect()
                # アクセストークンの復号化
                access_token:str = await decrypt_password(decrypt_password=request.access_token.encode('utf-8'))
                # Discordのユーザ情報を取得
                discord_user = await get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            for guild in self.bot.guilds:
                if request.guild_id == guild.id:
                #if request.get('guild_id') == guild.id:
                    # サーバの権限を取得

                    category_dict,category_index = await sort_channels(channels=guild.channels)

                    #print(category_dict)
                    pprint.pprint(category_dict)
                    return {'messagfe':''}
                    permission = await return_permission(
                        guild_id=guild.id,
                        user_id=discord_user.id,
                        access_token=access_token
                    )
                    # 使用するデータベースのテーブル名
                    TABLE = f'guilds_line_channel_{guild.id}'

                    c:List[Dict] = await db.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={}
                    )



async def sort_channels(
    channels:List[GuildChannel]
) -> Tuple[
    Dict[str,List[GuildChannel]],
    Dict[str,List[GuildChannel]]
]:
    # カテゴリーチャンネルを抽出
    categorys = [
        chan
        for chan in channels
        if chan.type == ChannelType.category
    ]

    # 配列の長さをカテゴリー数+1にする(要素を入れるとappendをする際にすべてのlistに入ってしまう)
    category_list = [[] for _ in range((len(categorys) + 1))]
    print(len(category_list))

    category_index = dict()
    category_dict = dict()

    # カテゴリーソート
    categorys = sorted(categorys,key=lambda c:c.position)

    pprint.pprint(channels)

    for i,category in enumerate(categorys):
        for chan in channels:
            # カテゴリーチャンネルがある場合
            if chan.category_id == category.id:
                category_list[i].append(chan)
                print(f'{i}_{category.name}:{chan.name}')
            # カテゴリー所属がない場合、末尾に入れる
            elif chan.category_id == None and chan not in category_list[-1]:
                category_list[-1].append(chan)
                print(f'{i}_None:{chan.name}')

        # カテゴリー内のチャンネルごとにソート
        channel_cate = category_list[i]
        #pprint.pprint(category_list)
        category_list[i] = sorted(channel_cate,key=lambda cc:cc.position)
        #print(category_list[i])
        category_dict.update({
            str(category.id) : category_list[i]
        })

        category_index.update({
            str(category.id) : category
        })

    category_dict.update({
        'None' : category_list[-1]
    })

    return category_dict,category_index