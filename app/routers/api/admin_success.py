from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from pkg.permission import return_permission
from pkg.oauth_check import discord_get_profile
from pkg.post_user_check import user_checker
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser
from model_types.environ_conf import EnvConf

from model_types.post_json_type import AdminSuccessJson
from model_types.session_type import FastAPISession

DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

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
                'line_bot_permission'           :line_bot_permission_code,
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
                discord_user = await discord_get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            TABLE = 'guild_set_permissions'

            # デバッグモード
            if DEBUG_MODE:
                from model_types.discord_type.guild_permission import Permission
                permission = Permission()
                permission.administrator = True
            else:
                # サーバの権限を取得
                permission = await return_permission(
                    user_id=discord_user.id,
                    guild=[
                        guild
                        for guild in self.bot.guilds
                        if guild.id == admin_json.guild_id
                    ][0]
                )

            # 管理者ではない場合
            if permission.administrator == False:
                return JSONResponse(content={'message':'access token Unauthorized'})

            row_value = {
                'line_permission'               :admin_json.line_permission,
                'line_user_id_permission'       :admin_json.line_user_id_permission,
                'line_role_id_permission'       :admin_json.line_role_id_permission,
                'line_bot_permission'           :admin_json.line_bot_permission,
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
                import pprint
                pprint.pprint(row_value)
                await DB.update_row(
                    table_name=TABLE,
                    row_values=row_value,
                    where_clause={
                        'guild_id':admin_json.guild_id
                    }
                )
                pprint.pprint(
                    await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':admin_json.guild_id
                        }
                    )
                )

            return JSONResponse(content={'message':'success!!'})