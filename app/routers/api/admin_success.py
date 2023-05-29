from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import pickle_write
from routers.api.chack.post_user_check import user_checker
from routers.session_base.user_session import OAuthData,User

from core.pickes_save.guild_permissions_columns import GUILD_SET_COLUMNS

REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"


from core.db_pickle import *


DISCORD_BASE_URL = "https://discord.com/api"

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

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")


@router.post('/api/admin-success')
async def admin_post(
    request:Request
):
    form = await request.form()

    # OAuth2トークンが有効かどうか判断
    check_code = await user_checker(
        request=request,
        oauth_session=OAuthData(**request.session.get('oauth_data')),
        user_session=User(**request.session.get('user'))
    )
    
    if check_code == 302:
        return RedirectResponse(url=REDIRECT_URL,status_code=302)
    elif check_code == 400:
        return JSONResponse(content={"message": "Fuck You. You are an idiot."})

    TABLE = 'guild_set_permissions'

    # 各権限コード
    line_permission_code = form.get("line_permission_code")
    line_bot_permission_code = form.get("line_bot_permission_code")
    vc_permission_code = form.get("vc_permission_code")
    webhook_permission_code = form.get("webhook_permission_code")

    # ユーザidの取り出し
    line_user_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('member_select_line_')
    ]
    line_bot_user_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('member_select_line_bot_')
    ]
    vc_user_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('member_select_vc_')
    ]
    webhook_user_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('member_select_webhook_')
    ]

    # ロールidの取り出し
    line_role_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('role_select_line_')
    ]
    line_bot_role_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('role_select_line_bot_')
    ]
    vc_role_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('role_select_vc_')
    ]
    webhook_role_id_permission = [
        int(form.get(key))
        for key in form.keys()
        if key.startswith('role_select_webhook_')
    ]

    row_value = {
        'line_permission'               :line_permission_code,
        'line_user_id_permission'       :line_user_id_permission,
        'line_role_id_permission'       :line_role_id_permission,
        'line_bot_permission_code'      :line_bot_permission_code,
        'line_bot_user_id_permission'   :line_bot_user_id_permission,
        'line_bot_role_id_permission'   :line_bot_role_id_permission,
        'vc_permission'                 :vc_permission_code,
        'vc_user_id_permission'         :vc_user_id_permission,
        'vc_role_id_permission'         :vc_role_id_permission,
        'webhook_permission'            :webhook_permission_code,
        'webhook_user_id_permission'    :webhook_user_id_permission,
        'webhook_role_id_permission'    :webhook_role_id_permission
    }

    await db.connect()

    await db.update_row(
        table_name=TABLE,
        row_values=row_value,
        where_clause={
            'guild_id':form.get('guild_id')
        }
    )

    # 更新後のテーブルを取得
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
        'api/adminsuccess.html',
        {
            'request': request,
            'guild_id': form['guild_id'],
            'title':'成功'
        }
    )
