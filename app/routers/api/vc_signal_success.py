from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from pkg.permission import return_permission
from pkg.oauth_check import discord_get_profile
from pkg.post_user_check import user_checker
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser

from model_types.table_type import GuildSetPermission
from model_types.post_json_type import VcSignalSuccessJson
from model_types.session_type import FastAPISession
from model_types.environ_conf import EnvConf

from core.auto_db_creator.vc_columns import VC_COLUMNS

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL
DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class VcSignalSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/vc-signal-success')
        async def vc_post(
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

            # 使用するデータベースのテーブル名
            TABLE = f'guilds_vc_signal'

            # "send_channel_id_"で始まるキーのみを抽出し、数字部分を取得する
            numbers = [
                int(key.replace("send_channel_id_", ""))
                for key in form.keys()
                if key.startswith("send_channel_id_")
            ]

            row_list = []

            # チャンネルごとに更新をかける
            for vc_id in numbers:
                row_values = {}
                send_signal = False
                join_bot = False
                everyone_mention = False
                role_key = [
                    int(form.get(key))
                    for key in form.keys()
                    if key.startswith(f"role_{vc_id}_")
                ]

                if form.get(f"send_signal_{vc_id}") != None:
                    send_signal = True
                if form.get(f"join_bot_{vc_id}") != None:
                    join_bot = True
                if form.get(f"everyone_mention_{vc_id}") != None:
                    everyone_mention = True

                row_values = {
                    'send_signal':send_signal,
                    'send_channel_id':form.get(f"send_channel_id_{vc_id}"),
                    'join_bot':join_bot,
                    'everyone_mention':everyone_mention,
                    'mention_role_id':role_key
                }

                where_clause = {
                    'vc_id': vc_id
                }

                row_list.append({
                    'where_clause':where_clause,
                    'row_values':row_values
                })

            #print(row_list)

            if DB.conn == None:
                await DB.connect()

            await DB.primary_batch_update_rows(
                table_name=TABLE,
                set_values_and_where_columns=row_list,
                table_colum=VC_COLUMNS
            )

            return templates.TemplateResponse(
                'api/vcsignalsuccess.html',
                {
                    'request': request,
                    'guild_id': form['guild_id'],
                    'title':'成功'
                }
            )

        @self.router.post('/api/vc-signal-success-json')
        async def vc_post(
            vc_signal_json:VcSignalSuccessJson,
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
                discord_user = await discord_get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            ADMIN_TABLE = 'guild_set_permissions'

            for guild in self.bot.guilds:
                if vc_signal_json.guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE == False:
                        # サーバの権限を取得
                        permission = await return_permission(
                            user_id=discord_user.id,
                            guild=[
                                guild
                                for guild in self.bot.guilds
                                if guild.id == vc_signal_json.guild_id
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
                        vc_signal_per = GuildSetPermission(**per[0])
                        permission_code = await permission.get_permission_code()

                        # 編集可能かどうか
                        if((vc_signal_per.vc_permission & permission_code) or
                        discord_user.id in vc_signal_per.line_user_id_permission or
                        len(set(member_roles) & set(vc_signal_per.line_role_id_permission))):
                            pass
                        else:
                            return JSONResponse(content={'message':'access token Unauthorized'})

                    # 使用するデータベースのテーブル名
                    TABLE = f'guilds_vc_signal'

                    for vc in vc_signal_json.vc_channel_list:
                        row_value = {
                            'send_signal'       :vc.send_signal,
                            'send_channel_id'   :vc.send_channel_id,
                            'join_bot'          :vc.join_bot,
                            'everyone_mention'  :vc.everyone_mention,
                            'mention_role_id'   :vc.mention_role_id
                        }
                        # デバッグモード
                        if DEBUG_MODE == False:
                            await DB.update_row(
                                table_name=TABLE,
                                row_values=row_value,
                                where_clause={
                                    'vc_id':vc.vc_id
                                }
                            )
                        else:
                            import pprint
                            pprint.pprint(row_value)

                    return JSONResponse(content={'message':'success!!'})

