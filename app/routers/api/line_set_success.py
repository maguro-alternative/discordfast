from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from base.aio_req import pickle_write,return_permission,get_profile,decrypt_password,encrypt_password

from routers.api.chack.post_user_check import user_checker
from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser

from model_types.table_type import GuildSetPermission
from model_types.post_json_type import LineSetSuccessJson
from model_types.session_type import FastAPISession

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import DB

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"
ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class LineSetSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/line-set-success')
        async def line_set_success(request: Request):

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

            TABLE = f'line_bot'

            hashed_notify_token:bytes = await encrypt_password(form.get('line_notify_token'))
            hashed_bot_token:bytes = await encrypt_password(form.get('line_bot_token'))
            hashed_bot_secret:bytes = await encrypt_password(form.get('line_bot_secret'))
            hashed_group_id:bytes = await encrypt_password(form.get('line_group_id'))
            hashed_client_id:bytes = await encrypt_password(form.get('line_client_id'))
            hashed_client_secret:bytes = await encrypt_password(form.get('line_client_secret'))
            default_channel_id:int = form.get('default_channel_id')
            debug_mode:bool = bool(form.get('debug_mode',default=False))

            row_values = {
                'line_notify_token':hashed_notify_token,
                'line_bot_token':hashed_bot_token,
                "line_bot_secret":hashed_bot_secret,
                'line_group_id':hashed_group_id,
                'line_client_id': hashed_client_id,
                'line_client_secret': hashed_client_secret,
                'default_channel_id':default_channel_id,
                'debug_mode':debug_mode
            }

            if DB.conn == None:
                await DB.connect()
            await DB.update_row(
                table_name=TABLE,
                row_values=row_values,
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
                'api/linesetsuccess.html',
                {
                    'request': request,
                    'guild_id': form['guild_id'],
                    'title':'成功'
                }
            )

        @self.router.post('/api/line-set-success-json')
        async def line_set_success(
            line_set_json: LineSetSuccessJson,
            request: Request
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

            ADMIN_TABLE = 'guild_set_permissions'

            for guild in self.bot.guilds:
                if line_set_json.guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE == False:
                        # サーバの権限を取得
                        permission = await return_permission(
                            guild_id=guild.id,
                            user_id=discord_user.id,
                            access_token=access_token
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
                        line_bot_per = GuildSetPermission(**per[0])
                        permission_code = await permission.get_permission_code()

                        # 編集可能かどうか
                        if((line_bot_per & permission_code) and
                        discord_user.id in line_bot_per.line_bot_user_id_permission and
                        len(set(member_roles) & set(line_bot_per.line_bot_role_id_permission))):
                            pass
                        else:
                            return JSONResponse(content={'message':'access token Unauthorized'})
                    else:
                        from model_types.discord_type.guild_permission import Permission
                        permission = Permission()
                        permission.administrator = True

                    TABLE = 'line_bot'

                    row_value = {
                        'default_channel_id':line_set_json.default_channel_id,
                        'debug_mode'        :line_set_json.debug_mode
                    }

                    # 変更があった場合に追加
                    # 同時に暗号化も行う
                    if line_set_json.line_notify_token:
                        if len(line_set_json.line_notify_token) > 30:
                            row_value.update({'line_notify_token':await encrypt_password(line_set_json.line_notify_token)})
                    if line_set_json.line_bot_token:
                        if len(line_set_json.line_bot_token) > 30:
                            row_value.update({'line_bot_token':await encrypt_password(line_set_json.line_bot_token)})
                    if line_set_json.line_bot_secret:
                        if len(line_set_json.line_bot_secret) > 30:
                            row_value.update({'line_bot_secret':await encrypt_password(line_set_json.line_bot_secret)})
                    if line_set_json.line_group_id:
                        if len(line_set_json.line_group_id) > 30:
                            row_value.update({'line_group_id':await encrypt_password(line_set_json.line_group_id)})
                    if line_set_json.line_client_id:
                        if len(line_set_json.line_client_id) > 9:
                            row_value.update({'line_client_id':await encrypt_password(line_set_json.line_client_id)})
                    if line_set_json.line_client_secret:
                        if len(line_set_json.line_client_secret) > 30:
                            row_value.update({'line_client_secret':await encrypt_password(line_set_json.line_client_secret)})

                    # デバッグモード
                    if DEBUG_MODE == False:
                        await DB.update_row(
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