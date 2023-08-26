from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.database import PostgresDB
from base.aio_req import pickle_write,return_permission,get_profile,decrypt_password
from routers.api.chack.post_user_check import user_checker
from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser
from model_types.post_json_type import AdminSuccessJson
from model_types.session_type import FastAPISession

from core.pickes_save.guild_permissions_columns import GUILD_SET_COLUMNS

DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import DB

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class AdminSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/admin-success')
        async def admin_post(
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
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
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

            if DB.conn == None:
                await DB.connect()

            await DB.update_row(
                table_name=TABLE,
                row_values=row_value,
                where_clause={
                    'guild_id':form.get('guild_id')
                }
            )

            # 更新後のテーブルを取得
            table_fetch = await DB.select_rows(
                table_name=TABLE,
                columns=[],
                where_clause={}
            )

            #await DB.disconnect()

            # pickleファイルに書き込み
            #await pickle_write(filename=TABLE,table_fetch=table_fetch)

            return templates.TemplateResponse(
                'api/adminsuccess.html',
                {
                    'request': request,
                    'guild_id': form['guild_id'],
                    'title':'成功'
                }
            )

        @self.router.post('/api/admin-success-json')
        async def admin_post_json(
            admin_json  :AdminSuccessJson,
            request     :Request
        ):
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token:str = session.discord_oauth_data.access_token
                # Discordのユーザ情報を取得
                discord_user = await get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            TABLE = 'guild_set_permissions'

            # デバッグモード
            if DEBUG_MODE == False:
                # サーバの権限を取得
                permission = await return_permission(
                    guild_id=admin_json.guild_id,
                    user_id=discord_user.id,
                    access_token=access_token
                )
            else:
                from model_types.discord_type.guild_permission import Permission
                permission = Permission()
                permission.administrator = True

            # 管理者ではない場合
            if permission.administrator == False:
                return JSONResponse(content={'message':'access token Unauthorized'})

            row_value = {
                'line_permission'               :admin_json.line_permission,
                'line_user_id_permission'       :admin_json.line_user_id_permission,
                'line_role_id_permission'       :admin_json.line_role_id_permission,
                'line_bot_permission_code'      :admin_json.line_bot_permission,
                'line_bot_user_id_permission'   :admin_json.line_bot_user_id_permission,
                'line_bot_role_id_permission'   :admin_json.line_bot_role_id_permission,
                'vc_permission'                 :admin_json.vc_permission,
                'vc_user_id_permission'         :admin_json.vc_user_id_permission,
                'vc_role_id_permission'         :admin_json.vc_role_id_permission,
                'webhook_permission'            :admin_json.webhook_permission,
                'webhook_user_id_permission'    :admin_json.webhook_user_id_permission,
                'webhook_role_id_permission'    :admin_json.webhook_role_id_permission
            }

            # デバッグモード
            if DEBUG_MODE == False:
                await DB.update_row(
                    table_name=TABLE,
                    row_values=row_value,
                    where_clause={
                        'guild_id':admin_json.guild_id
                    }
                )
            else:
                import pprint
                pprint.pprint(row_value)

            return JSONResponse(content={'message':'success!!'})