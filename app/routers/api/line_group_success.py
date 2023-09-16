from fastapi import APIRouter,HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

import os

from typing import List,Dict

from base.aio_req import (
    aio_get_request,
    decrypt_password,
    line_oauth_check
)

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_pickle import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_pickle import DB

from model_types.line_type.line_message import LineBotAPI
from model_types.discord_type.message_creater import ReqestDiscord
from model_types.table_type import LineBotColunm

from model_types.post_json_type import LineGroupSuccessJson
from model_types.line_type.line_oauth import LineTokenVerify,LineProfile
from model_types.session_type import FastAPISession

LINE_OAUTH_BASE_URL = "https://api.line.me/oauth2/v2.1"
LINE_BOT_URL = 'https://api.line.me/v2/bot'

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.environ.get('DISCORD_CLIENT_ID')}&scope={os.environ.get('DISCORD_SCOPE')}&redirect_uri={os.environ.get('DISCORD_CALLBACK_URL')}&prompt=consent"
ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

# デバッグモード
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))

class LineGroupSuccess(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.post('/api/line-group-success')
        async def line_group_success(request: Request):

            TABLE = "line_bot"

            token_valid:bool = await line_oauth_check(
                access_token=request.session['line_oauth_data']['access_token']
            )

            if token_valid == False:
                return JSONResponse(content={'message':'access token Unauthorized'})

            form = await request.form()
            default_channel_id:int = int(form.get('default_channel_id'))

            if DB.conn == None:
                await DB.connect()
            await DB.update_row(
                table_name=TABLE,
                row_values={
                    'default_channel_id':default_channel_id
                },
                where_clause={
                    'guild_id':form.get('guild_id')
                }
            )
            # 更新後のテーブルを取得
            table_fetch:List[dict] = await DB.select_rows(
                table_name=TABLE,
                columns=[],
                where_clause={}
            )

            bot_info:List[dict] = [
                bot
                for bot in table_fetch #line_bot_fetch
                if int(bot.get('guild_id')) == int(form.get('guild_id'))
            ]

            line_notify_token:str = await decrypt_password(encrypted_password=bytes(bot_info[0].get('line_notify_token')))
            line_bot_token:str = await decrypt_password(encrypted_password=bytes(bot_info[0].get('line_bot_token')))

            line_group_id:str = await decrypt_password(encrypted_password=bytes(bot_info[0].get('line_group_id')))

            # LINEのインスタンスを作成
            line_bot_api = LineBotAPI(
                notify_token=line_notify_token,
                line_bot_token=line_bot_token,
                line_group_id=line_group_id
            )

            # Discordのインスタンスを作成
            discord_bot_api = ReqestDiscord(
                guild_id=int(form.get('guild_id')),
                limit=100,
                token=os.environ["DISCORD_BOT_TOKEN"]
            )

            # LINEのユーザ名
            user_name:str = request.session['line_user']['name']
            # Discordのチャンネル名
            default_channel_info = await discord_bot_api.channel_info_get(
                channel_id=default_channel_id
            )

            # 変更URL
            url = (os.environ.get('LINE_CALLBACK_URL').replace('/line-callback/','')) + f'/group/{form.get("guild_id")}'

            change_text = f"{user_name}によりDiscordへの送信先が「{default_channel_info.name}」に変更されました。"
            change_text += f"\n変更はこちらから\n{url}"

            # 通知するチェックボックスが入っていた場合
            if form.get('chenge_alert') != None:
                # LINEとDiscord双方に変更を送信
                await line_bot_api.push_message_notify(
                    message=change_text
                )
                await discord_bot_api.send_discord(
                    channel_id=default_channel_id,
                    message=change_text
                )

            return templates.TemplateResponse(
                'api/linesetsuccess.html',
                {
                    'request': request,
                    'guild_id': form['guild_id'],
                    'title':'成功'
                }
            )

        @self.router.post('/api/line-group-success-json')
        async def line_group_success(
            request: Request,
            line_group_json: LineGroupSuccessJson
        ):
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token:str = session.line_oauth_data.access_token
                # LINEのユーザ情報を取得
                line_user = await aio_get_request(
                    url=f"{LINE_OAUTH_BASE_URL}/verify?access_token={access_token}",
                    headers={}
                )
                line_user = LineTokenVerify(**line_user)

                # トークンが無効
                if line_user.error != None:
                    return JSONResponse(content={'message':'access token Unauthorized'})
            else:
                line_user = {
                    'scope'     :'profile%20openid%20email',
                    'client_id' :'0',
                    'expires_in':100
                }
                line_user = LineTokenVerify(**line_user)

            TABLE = "line_bot"

            for guild in self.bot.guilds:
                if line_group_json.guild_id == guild.id:
                    l = await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':line_group_json.guild_id
                        }
                    )

                    line_bot_table = LineBotColunm(**l[0])

                    # 復号化
                    line_group_id:str = await decrypt_password(encrypted_password=bytes(line_bot_table.line_group_id))
                    line_bot_token:str = await decrypt_password(encrypted_password=bytes(line_bot_table.line_bot_token))
                    line_notify_token:str = await decrypt_password(encrypted_password=bytes(line_bot_table.line_notify_token))
                    # デバッグモード
                    if DEBUG_MODE == False:
                        # グループIDが有効かどうか判断
                        r = await aio_get_request(
                            url=f"{LINE_BOT_URL}/group/{line_group_id}/member/{session.line_user.sub}",
                            headers={
                                'Authorization': f'Bearer {line_bot_token}'
                            }
                        )
                        line_group_profile = LineProfile(**r)
                        # グループIDが無効の場合、友達から判断
                        if line_group_profile.message != None:
                            raise HTTPException(status_code=400, detail="認証失敗")
                    else:
                        r = {
                            'displayName'   :'test',
                            'userId'        :'aaa',
                            'pictureUrl'    :'png'
                        }
                        line_group_profile = LineProfile(**r)

                    row_value = {
                        'default_channel_id':line_bot_table.default_channel_id
                    }

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

                    if line_group_json.change_alert:
                        # 変更URL
                        #url = (os.environ.get('LINE_CALLBACK_URL').replace('/line-callback/','')) + f'/group/'

                        change_text = f"{line_group_profile.displayName}によりDiscordへの送信先が「{guild.get_channel_or_thread(line_group_json.default_channel_id).name}」に変更されました。"
                        #change_text += f"\n変更はこちらから\n{url}"

                        # LINEのインスタンスを作成
                        line_bot_api = LineBotAPI(
                            notify_token=line_notify_token,
                            line_bot_token=line_bot_token,
                            line_group_id=line_group_id
                        )
                        # LINEとDiscord双方に変更を送信
                        await line_bot_api.push_message_notify(
                            message=change_text
                        )
                        send_channel = guild.get_channel_or_thread(line_group_json.default_channel_id)

                        await send_channel.send(change_text)

                    return JSONResponse(content={'message':'success!!'})