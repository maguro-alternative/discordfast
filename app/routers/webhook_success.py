from fastapi import APIRouter
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os
import re
import uuid

from base.database import PostgresDB
from core.db_pickle import *

import aiofiles
import pickle

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
async def line_post(
    request:Request
):
    form = await request.form()

    TABLE = f'webhook_{form.get("guild_id")}'

    await db.connect()

    FORM_NAMES = (
        "webhookSelect_",
        "subscType_",
        "subscId_",
        "role_role_select_",
        "searchOrText",
        "searchAndText",
        "mentionOrText",
        "mentionAndText",

        "webhookChange_",
        "subscTypeChange_",
        "subscIdChange_",
        "change_role_select_",
        "changeSearchOrText",
        "changeSearchAndText",
        "changeMentionOrText",
        "changeMentionAndText"
    )

    # "webhookSelect_"で始まるキーのみを抽出し、数字部分を取得する
    create_webhook_number = [
        int(key.replace(FORM_NAMES[0], "")) 
        for key in form.keys() 
        if key.startswith(FORM_NAMES[0])
    ]

    # "webhookChange_"で始まるキーのみを抽出し、数字部分を取得する
    change_webhook_number = [
        int(key.replace(FORM_NAMES[8], "")) 
        for key in form.keys() 
        if key.startswith(FORM_NAMES[8])
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
            'subscription_id': form.get(f"{FORM_NAMES[1]}{webhook_num}"),
            'subscription_type':form.get(f"{FORM_NAMES[2]}{webhook_num}"),
        }

        # 入力漏れがあった場合
        if (len(form.get(f"{FORM_NAMES[1]}{webhook_num}")) == 0 or 
            len(form.get(f"{FORM_NAMES[2]}{webhook_num}")) == 0):
            none_flag = True

        for row_name,form_name in {
            'mention_roles':FORM_NAMES[3],
            'search_or_word':FORM_NAMES[4],
            'search_and_word':FORM_NAMES[5],
            'mention_or_word':FORM_NAMES[6],
            'mention_and_word':FORM_NAMES[7]
        }.items():
            row_list = list()
            role_list = list()

            # キーの数字を取り除いたキー名を格納するリストを作成
            key_list = list()
            for key in form.keys():
                if f'{form_name}{webhook_num}_' in key:
                    key_name = re.search(r'\d+$', key)  # キーから数字を取り除く
                    key_list.append(int(key_name.group()))
                    # print(key)

            for key in key_list:
                # print(key,form.get(f'{form_name}{webhook_num}_{key}'))
                if form_name == 'mention_roles':
                    role_list.append(int(form.get(f'{form_name}{webhook_num}_{key}')))
                    # 最後の要素の場合、dictに代入
                    if key == key_list[-1]:
                        row_list.append(role_list)
                else:
                    row_list.append(form.get(f'{form_name}{webhook_num}_{key}'))

            row.update({
                row_name:row_list
            })

            # print(row)

        # 必須のものに抜けがない場合、テーブルに追加
        if none_flag == False:
            create_webhook_list.append(row)

    #print(create_webhook_list)

    # まとめて追加
    if len(create_webhook_list) > 0:
        await db.batch_insert_row(
            table_name=TABLE,
            row_values=create_webhook_list
        )

    for webhook_num in change_webhook_number:
        row = {
            'guild_id': int(form.get("guild_id")), 
            'webhook_id':int(form.get(f"{FORM_NAMES[8]}{webhook_num}")),
            'subscription_id': form.get(f"{FORM_NAMES[9]}{webhook_num}"),
            'subscription_type':form.get(f"{FORM_NAMES[10]}{webhook_num}"),
        }

        for row_name,form_name in {
            'mention_roles':FORM_NAMES[11],
            'search_or_word':FORM_NAMES[12],
            'search_and_word':FORM_NAMES[13],
            'mention_or_word':FORM_NAMES[14],
            'mention_and_word':FORM_NAMES[15]
        }.items():
            row_list = list()
            role_list = list()
            # キーの数字を取り除いたキー名を格納するリストを作成
            key_list = list()
            for key in form.keys():
                if f'{form_name}{webhook_num}_' in key:
                    key_name = re.search(r'\d+$', key)  # キーから数字を取り除く
                    key_list.append(int(key_name.group()))

            for key in key_list:
                if form_name == 'mention_roles':
                    role_list.append(int(form.get(f'{form_name}{webhook_num}_{key}')))
                    # 最後の要素の場合、dictに代入
                    if key == key_list[-1]:
                        row_list.append(role_list)
                else:
                    row_list.append(form.get(f'{form_name}{webhook_num}_{key}'))

            row.update({
                row_name:row_list
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

    # 取り出して書き込み
    dict_row = [
        dict(zip(record.keys(), record)) 
        for record in table_fetch
    ]

    # 書き込み
    async with aiofiles.open(
        file=f'{TABLE}.pickle',
        mode='wb'
    ) as f:
        await f.write(pickle.dumps(obj=dict_row))

    return templates.TemplateResponse(
        'webhooksuccess.html',
        {
            'request': request,
            'guild_id': form['guild_id'],
            'title':'成功'
        }
    )