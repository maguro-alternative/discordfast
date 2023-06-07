from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
import re
import uuid
from datetime import datetime,timezone

from base.database import PostgresDB
from base.aio_req import pickle_write
from core.db_pickle import *
from core.pickes_save.webhook_columns import WEBHOOK_COLUMNS

from routers.api.chack.post_user_check import user_checker
from routers.session_base.user_session import DiscordOAuthData,DiscordUser

REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_BASE_URL = "https://discord.com/api"

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


router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.post('/api/webhook-success')
async def webhook_post(
    request:Request
):
    form = await request.form()

    # OAuth2トークンが有効かどうか判断
    check_code = await user_checker(
        request=request,
        oauth_session=DiscordOAuthData(**request.session.get('discord_oauth_data')),
        user_session=DiscordUser(**request.session.get('discord_user'))
    )
    
    if check_code == 302:
        return RedirectResponse(url=REDIRECT_URL,status_code=302)
    elif check_code == 400:
        return JSONResponse(content={"message": "Fuck You. You are an idiot."})

    TABLE = f'webhook_{form.get("guild_id")}'

    await db.connect()

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
        #uuid_uint64 = int.from_bytes(uuid_val.bytes, byteorder='big', signed=False)
        row = {
            'uuid':uuid_val,
            'guild_id': int(form.get("guild_id")), 
            'webhook_id':int(form.get(f"{FORM_NAMES[0]}{webhook_num}")),
            'subscription_type':form.get(f"{FORM_NAMES[1]}{webhook_num}"),
            'subscription_id': form.get(f"{FORM_NAMES[2]}{webhook_num}")
        }

        print(row)

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
                #print(f'{form_name}{webhook_num}_{key}',form.get(f'{form_name}{webhook_num}_{key}'))

            row.update({
                row_name:row_list
            })

            # print(row)
        
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
        await db.batch_insert_row(
            table_name=TABLE,
            row_values=create_webhook_list
        )
    #print(create_webhook_list)

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
        await db.primary_batch_update_rows(
            table_name=TABLE,
            set_values_and_where_columns=change_webhook_list,
            table_colum=WEBHOOK_COLUMNS
        )

    # 削除
    for del_num in del_webhook_numbers:
        await db.delete_row(
            table_name=TABLE,
            where_clause={
                'uuid':form.get(f'uuid_{del_num}')
            }
        )

    table_fetch = await db.select_rows(
        table_name=TABLE,
        columns=[],
        where_clause={}
    )

    await db.disconnect()
    
    # pickleファイルに書き込み
    await pickle_write(
        filename=TABLE,
        table_fetch=table_fetch
    )

    return templates.TemplateResponse(
        'api/webhooksuccess.html',
        {
            'request': request,
            'guild_id': form['guild_id'],
            'title':'成功'
        }
    )