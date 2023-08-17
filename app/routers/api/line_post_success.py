from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
import re

from base.database import PostgresDB
from base.aio_req import pickle_write,return_permission,get_profile,decrypt_password
from core.db_pickle import *
from routers.api.chack.post_user_check import user_checker
from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser

from model_types.table_type import GuildSetPermission
from model_types.post_json_type import LinePostSuccessJson

from core.pickes_save.line_columns import LINE_COLUMNS

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import db
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import db

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class LinePostSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/line-post-success')
        async def line_post_success(request: Request):

            form = await request.form()

            # OAuth2トークンが有効かどうか判断
            check_code = await user_checker(
                request=request,
                oauth_session=DiscordOAuthData(**request.session.get('discord_oauth_data')),
                user_session=DiscordUser(**request.session.get('discord_user'))
            )

            if check_code == 302:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            elif check_code == 400:
                return JSONResponse(content={"message": "Fuck You. You are an idiot."})

            TABLE = f'guilds_line_channel_{form["guild_id"]}'

            FORM_NAMES = (
                "line_ng_channel_",
                "message_bot_",
                "default_",
                "recipient_add_",
                "pins_add_",
                "member_"
            )

            # "line_ng_channel_"で始まるキーのみを抽出し、数字部分を取得する
            line_ng_message_numbers = [
                int(key.replace(FORM_NAMES[0], ""))
                for key in form.keys()
                if key.startswith(FORM_NAMES[0])
            ]

            # "message_bot_"で始まるキーのみを抽出し、数字部分を取得する
            message_bot_numbers = [
                int(key.replace(FORM_NAMES[1], ""))
                for key in form.keys()
                if key.startswith(FORM_NAMES[1])
            ]

            # "default_"で始まるキーのみを抽出し、数字部分を取得する
            default_numbers = [
                int(key.replace(FORM_NAMES[2], ""))
                for key in form.keys()
                if key.startswith(FORM_NAMES[2])
            ]

            # "recipient_add_"で始まるキーのみを抽出し、数字部分を取得する
            recipient_add_numbers = [
                int(key.replace(FORM_NAMES[3], ""))
                for key in form.keys()
                if key.startswith(FORM_NAMES[3])
            ]

            # "pins_add_"で始まるキーのみを抽出し、数字部分を取得する
            pins_add_numbers = [
                int(key.replace(FORM_NAMES[4], ""))
                for key in form.keys()
                if key.startswith(FORM_NAMES[4])
            ]

            # "member_"で始まるキーのみを抽出し、数字部分を取得する
            # 後ろにあるナンバーと_をre.searchで取り除く
            member_numbers = [
                int(re.search(r'\d+',key.replace(FORM_NAMES[5], "")).group())
                for key in form.keys()
                if key.startswith(FORM_NAMES[5])
            ]

            # 重複している要素を取り除き、変更があったチャンネルのみを取り出す
            change_number = set(
                line_ng_message_numbers +
                message_bot_numbers +
                default_numbers +
                recipient_add_numbers +
                pins_add_numbers +
                member_numbers
            )

            row_list = []

            for channel_id in change_number:
                row_values = {}
                message_type_list = []
                for form_name in FORM_NAMES:
                    # 存在する(更新された)場合
                    if form.get(f"{form_name}{channel_id}") != None:
                        if form_name == FORM_NAMES[0]:
                            row_values.update({
                                'line_ng_channel':bool(form.get(f"{form_name}{channel_id}"))
                            })
                        if form_name == FORM_NAMES[1]:
                            row_values.update({
                                'message_bot':bool(form.get(f"{form_name}{channel_id}"))
                            })

                        # いずれかのメッセージタイプに該当した場合
                        if form_name in [
                            FORM_NAMES[2],
                            FORM_NAMES[3],
                            FORM_NAMES[4]
                        ]:
                            message_type_list.append(form.get(f"{form_name}{channel_id}"))
                            row_values.update({
                                'ng_message_type':message_type_list
                            })
                    # 送信しないユーザの場合
                    elif form_name == FORM_NAMES[5] and form.get(f'{form_name}{channel_id}_1') != None:
                        ng_users = []
                        i:int = 1
                        # 該当するものが無くなるまで繰り返す
                        while form.get(f'{form_name}{channel_id}_{i}') != None:
                            ng_users.append(form.get(f'{form_name}{channel_id}_{i}'))
                            i = i + 1
                        row_values.update({
                            'ng_users':ng_users
                        })
                    # Falseが選択されている場合
                    elif form_name in [FORM_NAMES[0],FORM_NAMES[1]]:
                        row_values.update({
                            'line_ng_channel':False,
                            'message_bot':False
                        })

                # 更新する
                row_list.append({
                    'where_clause':{
                        'channel_id':channel_id
                    },
                    'row_values':row_values
                })


            if db.conn == None:
                await db.connect()
            await db.primary_batch_update_rows(
                table_name=TABLE,
                set_values_and_where_columns=row_list,
                table_colum=LINE_COLUMNS
            )
            # 更新後のテーブルを取得
            table_fetch = await db.select_rows(
                table_name=TABLE,
                columns=[],
                where_clause={}
            )
            #await db.disconnect()

            # pickleファイルに書き込み
            #await pickle_write(filename=TABLE,table_fetch=table_fetch)

            return templates.TemplateResponse(
                'api/linepostsuccess.html',
                {
                    'request': request,
                    'guild_id': form['guild_id'],
                    'title':'成功'
                }
            )

        @self.router.post('/api/line-post-success-json')
        async def line_post_success(request: LinePostSuccessJson):
            if db.conn == None:
                await db.connect()

            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token:str = await decrypt_password(decrypt_password=request.access_token.encode('utf-8'))
                # Discordのユーザ情報を取得
                discord_user = await get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            ADMIN_TABLE = 'guild_set_permissions'

            for guild in self.bot.guilds:
                if request.guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE == False:
                        # サーバの権限を取得
                        permission = await return_permission(
                            guild_id=guild.id,
                            user_id=discord_user.id,
                            access_token=access_token
                        )
                        per = await db.select_rows(
                            table_name=ADMIN_TABLE,
                            columns=[],
                            where_clause={
                                'guild_id':guild.id
                            }
                        )
                        member_roles = [
                            role.id
                            for role in guild.get_member(discord_user.id).roles
                        ]
                        line_post_per = GuildSetPermission(**per[0])
                        permission_code = await permission.get_permission_code()

                        # 編集可能かどうか
                        if((line_post_per & permission_code) and
                        discord_user.id in line_post_per.line_user_id_permission and
                        len(set(member_roles) & set(line_post_per.line_role_id_permission))):
                            pass
                        else:
                            return JSONResponse(content={'message':'access token Unauthorized'})
                    else:
                        from model_types.discord_type.guild_permission import Permission
                        permission = Permission()
                        permission.administrator = True

                    TABLE = f'guilds_line_channel_{guild.id}'

                    for post_channel in request.channel_list:
                        row_value = {
                            'line_ng_channel'   :post_channel.line_ng_channel,
                            'ng_message_type'   :post_channel.ng_message_type,
                            'message_bot'       :post_channel.message_bot,
                            'ng_users'          :post_channel.ng_users
                        }
                        # デバッグモード
                        if DEBUG_MODE == False:
                            await db.update_row(
                                table_name=TABLE,
                                row_values=row_value,
                                where_clause={
                                    'channel_id':post_channel.channel_id
                                }
                            )
                        else:
                            import pprint
                            pprint.pprint(row_value)

                    return JSONResponse(content={'message':'success!!'})