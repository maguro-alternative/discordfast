from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

import re
import uuid
from datetime import datetime,timezone

from pkg.permission import return_permission
from pkg.oauth_check import discord_get_profile

from core.auto_db_creator.webhook_columns import WEBHOOK_COLUMNS

from pkg.post_user_check import user_checker
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser

from model_types.table_type import GuildSetPermission,WebhookSet
from model_types.post_json_type import WebhookSuccessJson
from model_types.session_type import FastAPISession
from model_types.environ_conf import EnvConf

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN
DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class WebhookSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/webhook-success')
        async def webhook_post(
            request:Request
        ):
            form = await request.form()

            # OAuth2トークンが有効かどうか判断
            check_code = await user_checker(
                oauth_session=DiscordOAuthData(**request.session.get('discord_oauth_data')),
                user_session=DiscordUser(**request.session.get('discord_user')),
                guild=[
                    guild
                    for guild in self.bot.guilds
                    if guild.id == int(form.get('guild_id'))
                ][0]
            )

            if check_code == 302:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            elif check_code == 400:
                return JSONResponse(content={"message": "Fuck You. You are an idiot."})

            TABLE = f'webhook_set'

            if DB.conn == None:
                await DB.connect()

            FORM_NAMES = (
                "webhookSelect_",
                "subscType_",
                "subscId_",             #2
                "role_role_select_",
                "member_member_select_",
                "searchOrText",
                "searchAndText",
                "ngOrText",
                "ngAndText",
                "mentionOrText",
                "mentionAndText",

                "webhookChange_",
                "subscTypeChange_",
                "subscIdChange_",       #13
                "role_role_change_",
                "member_member_change_",
                "changeSearchOrText",
                "changeSearchAndText",
                "changeNgOrText",
                "changeNgAndText",
                "changeMentionOrText",
                "changeMentionAndText"
            )

            # "webhookSelect_"で始まるキーのみを抽出し、数字部分を取得する
            # create_webhook_number = [1,2,3]
            create_webhook_number = [
                int(key.replace(FORM_NAMES[0], ""))
                for key in form.keys()
                if key.startswith(FORM_NAMES[0])
            ]

            # "webhookChange_"で始まるキーのみを抽出し、数字部分を取得する
            # change_webhook_number = [1,2,3]
            change_webhook_number = [
                int(key.replace(FORM_NAMES[11], ""))
                for key in form.keys()
                if key.startswith(FORM_NAMES[11])
            ]

            create_webhook_list = []

            change_webhook_list = []

            del_webhook_numbers = [
                int(del_key.replace("delWebhook_",""))
                for del_key in form.keys()
                if del_key.startswith("delWebhook_")
            ]

            # 新規作成
            for webhook_num in create_webhook_number:
                none_flag = False

                uuid_val = uuid.uuid4()
                row = {
                    'uuid':uuid_val,
                    'guild_id': int(form.get("guild_id")),
                    'webhook_id':int(form.get(f"{FORM_NAMES[0]}{webhook_num}")),
                    'subscription_type':form.get(f"{FORM_NAMES[1]}{webhook_num}"),
                    'subscription_id': form.get(f"{FORM_NAMES[2]}{webhook_num}")
                }

                # 入力漏れがあった場合
                if (len(form.get(f"{FORM_NAMES[1]}{webhook_num}")) == 0 or
                    len(form.get(f"{FORM_NAMES[2]}{webhook_num}")) == 0):
                    none_flag = True

                for row_name,form_name in {
                    'mention_roles'     :FORM_NAMES[3],
                    'mention_members'   :FORM_NAMES[4],
                    'search_or_word'    :FORM_NAMES[5],
                    'search_and_word'   :FORM_NAMES[6],
                    'ng_or_word'        :FORM_NAMES[7],
                    'ng_and_word'       :FORM_NAMES[8],
                    'mention_or_word'   :FORM_NAMES[9],
                    'mention_and_word'  :FORM_NAMES[10]
                }.items():
                    row_list = list()

                    # キーの数字を取り除いたキー名を格納するリストを作成
                    key_list = list()
                    for key in form.keys():
                        if f'{form_name}{webhook_num}_' in key:
                            key_name = re.search(r'\d+$', key)  # キーから数字を取り除く
                            key_list.append(int(key_name.group()))
                            # print(key)

                    for key in key_list:
                        row_list.append(form.get(f'{form_name}{webhook_num}_{key}'))

                    row.update({
                        row_name:row_list
                    })


                # 登録した時刻を登録
                now_time = datetime.now(timezone.utc)
                now_str = now_time.strftime('%a %b %d %H:%M:%S %z %Y')
                row.update({
                    'created_at':now_str
                })

                # 必須のものに抜けがない場合、テーブルに追加
                if none_flag == False:
                    create_webhook_list.append(row)

            # まとめて追加
            if len(create_webhook_list) > 0:
                await DB.batch_insert_row(
                    table_name=TABLE,
                    row_values=create_webhook_list
                )

            # 更新
            for webhook_num in change_webhook_number:
                row = {
                    'guild_id': int(form.get("guild_id")),
                    'webhook_id':int(form.get(f"{FORM_NAMES[11]}{webhook_num}")),
                    'subscription_type':form.get(f"{FORM_NAMES[12]}{webhook_num}"),
                    'subscription_id': form.get(f"{FORM_NAMES[13]}{webhook_num}")
                }

                for row_name,form_name in {
                    'mention_roles'     :FORM_NAMES[14],
                    'mention_members'   :FORM_NAMES[15],
                    'search_or_word'    :FORM_NAMES[16],
                    'search_and_word'   :FORM_NAMES[17],
                    'ng_or_word'        :FORM_NAMES[18],
                    'ng_and_word'       :FORM_NAMES[19],
                    'mention_or_word'   :FORM_NAMES[20],
                    'mention_and_word'  :FORM_NAMES[21]
                }.items():
                    row_list = list()

                    # キーの数字を取り除いたキー名を格納するリストを作成
                    key_list = list()
                    for key in form.keys():
                        if f'{form_name}{webhook_num}_' in key:
                            key_name = re.search(r'\d+$', key)  # キーから数字を取り除く
                            key_list.append(int(key_name.group()))

                    for key in key_list:
                        row_list.append(form.get(f'{form_name}{webhook_num}_{key}'))

                    row.update({
                        row_name:row_list
                    })

                # 時刻を引き継ぐ(csv形式への対応のため)
                row.update({
                    'created_at':form.get(f"created_time_{webhook_num}")
                })

                change_webhook_list.append({
                    'where_clause':{'uuid':form.get(f'uuid_{webhook_num}')},
                    'row_values':row
                })

            # まとめて更新
            if len(change_webhook_list) > 0:
                await DB.primary_batch_update_rows(
                    table_name=TABLE,
                    set_values_and_where_columns=change_webhook_list,
                    table_colum=WEBHOOK_COLUMNS
                )

            # 削除
            for del_num in del_webhook_numbers:
                await DB.delete_row(
                    table_name=TABLE,
                    where_clause={
                        'uuid':form.get(f'uuid_{del_num}')
                    }
                )

            table_fetch = await DB.select_rows(
                table_name=TABLE,
                columns=[],
                where_clause={}
            )

            return templates.TemplateResponse(
                'api/webhooksuccess.html',
                {
                    'request': request,
                    'guild_id': form['guild_id'],
                    'title':'成功'
                }
            )

        @self.router.post('/api/webhook-success-json')
        async def webhook_post(
            webhook_json:WebhookSuccessJson,
            request:Request
        ):
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()

            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token:str = session.discord_oauth_data.access_token
                # Discordのユーザ情報を取得
                discord_user = await discord_get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            ADMIN_TABLE = 'guild_set_permissions'

            for guild in self.bot.guilds:
                if webhook_json.guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE == False:
                        # サーバの権限を取得
                        permission = await return_permission(
                            user_id=discord_user.id,
                            guild=[
                                guild
                                for guild in self.bot.guilds
                                if guild.id == webhook_json.guild_id
                            ][0]
                        )
                        per = await DB.select_rows(
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
                        webhook_per = GuildSetPermission(**per[0])
                        permission_code = await permission.get_permission_code()

                        # 編集可能かどうか
                        if((webhook_per.webhook_permission & permission_code) or
                        discord_user.id in webhook_per.line_user_id_permission or
                        len(set(member_roles) & set(webhook_per.line_role_id_permission))):
                            pass
                        else:
                            return JSONResponse(content={'message':'access token Unauthorized'})

                    TABLE = f'webhook_set'

                    db_webhook = await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':guild.id
                        }
                    )

                    db_webhook = [
                        WebhookSet(**webhook)
                        for webhook in db_webhook
                    ]

                    db_webhook_id_list = [
                        webhook_id.uuid
                        for webhook_id in db_webhook
                    ]

                    # 登録した時刻を登録
                    now_time = datetime.now(timezone.utc)
                    now_str = now_time.strftime('%a %b %d %H:%M:%S %z %Y')

                    for webhook in webhook_json.webhook_list:
                        row_value = {
                            'webhook_id'        :webhook.webhook_id,
                            'subscription_type' :webhook.subscription_type,
                            'subscription_id'   :webhook.subscription_id,
                            'mention_roles'     :webhook.mention_roles,
                            'mention_members'   :webhook.mention_members,
                            'ng_or_word'        :webhook.ng_or_word,
                            'ng_and_word'       :webhook.ng_and_word,
                            'search_or_word'    :webhook.search_or_word,
                            'search_and_word'   :webhook.search_and_word,
                            'mention_or_word'   :webhook.mention_or_word,
                            'mention_and_word'  :webhook.mention_and_word
                        }
                        # 更新
                        if str(webhook.uuid) in db_webhook_id_list:
                            # デバッグモード
                            if DEBUG_MODE == False:
                                await DB.update_row(
                                    table_name=TABLE,
                                    row_values=row_value,
                                    where_clause={
                                        'uuid':webhook.uuid
                                    }
                                )

                        # 削除
                        elif webhook.delete_flag:
                            await DB.delete_row(
                                table_name=TABLE,
                                where_clause={
                                    'uuid':webhook.uuid
                                }
                            )

                        else:
                            uuid_val = uuid.uuid4()
                            row_value.update({
                                'uuid'      :uuid_val,
                                'guild_id'  :guild.id,
                                'created_at':now_str
                            })
                            # デバッグモード
                            if DEBUG_MODE == False:
                                await DB.insert_row(
                                    table_name=TABLE,
                                    row_values=row_value
                                )

                    return JSONResponse(content={'message':'success!!'})