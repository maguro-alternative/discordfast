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

from core.pickes_save.guild_permissions_columns import GUILD_SET_COLUMNS

DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"


from core.db_pickle import *

from discord.ext import commands
try:
    from core.start import DBot
except ModuleNotFoundError:
    from app.core.start import DBot

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

        @self.router.post('/api/admin-success-json')
        async def admin_post_json(
            request:AdminSuccessJson
        ):
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

            TABLE = 'guild_set_permissions'

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
                    else:
                        from model_types.discord_type.guild_permission import Permission
                        permission = Permission()
                        permission.administrator = True

                    row_value = {
                        'line_permission'               :request.line_permission,
                        'line_user_id_permission'       :request.line_user_id_permission,
                        'line_role_id_permission'       :request.line_role_id_permission,
                        'line_bot_permission_code'      :request.line_bot_permission,
                        'line_bot_user_id_permission'   :request.line_bot_user_id_permission,
                        'line_bot_role_id_permission'   :request.line_bot_role_id_permission,
                        'vc_permission'                 :request.vc_permission,
                        'vc_user_id_permission'         :request.vc_user_id_permission,
                        'vc_role_id_permission'         :request.vc_role_id_permission,
                        'webhook_permission'            :request.webhook_permission,
                        'webhook_user_id_permission'    :request.webhook_user_id_permission,
                        'webhook_role_id_permission'    :request.webhook_role_id_permission
                    }

                    # デバッグモード
                    if DEBUG_MODE == False:
                        await db.update_row(
                            table_name=TABLE,
                            row_values=row_value,
                            where_clause={
                                'guild_id':guild.id
                            }
                        )
                    else:
                        import pprint
                        pprint.pprint(row_value)

                    return JSONResponse(content={'message':'success!!'})