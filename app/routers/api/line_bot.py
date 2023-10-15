from fastapi import APIRouter,Request,Header
from fastapi.responses import HTMLResponse
from starlette.requests import Request

import base64
import hashlib
import hmac

try:
    from model_types.line_type.line_event import Line_Responses
    from model_types.discord_type.message_creater import ReqestDiscord
    from model_types.line_type.line_message import LineBotAPI
    from model_types.table_type import LineBotColunm
except ModuleNotFoundError:
    from app.model_types.line_type.line_event import Line_Responses
    from app.model_types.discord_type.message_creater import ReqestDiscord
    from app.model_types.line_type.line_message import LineBotAPI
    from app.model_types.table_type import LineBotColunm
# ./venv/Scripts/activate.bat

from typing import List

from pkg.crypt import decrypt_password

from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

from model_types.environ_conf import EnvConf

TOKEN = EnvConf.DISCORD_BOT_TOKEN
ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

class LineBotWebhook(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        # LINE側のメッセージを受け取る
        @self.router.post("/line-bot")
        async def line_response(
            response:Line_Responses,
            byte_body:Request,
            x_line_signature=Header(None)
        ) -> HTMLResponse:
            """
            response:Line_Responses
            LINEから受け取ったイベントの内容
            jsonがクラスに変換されている。

            byte_body:Request
            LINEから受け取ったイベントのバイナリデータ。
            LINEからのメッセージという署名の検証に必要。

            x_line_signature:Header
            LINEから受け取ったjsonのヘッダー。
            こちらも署名に必要。
            """

            # request.bodyを取得
            boo = await byte_body.body()
            body = boo.decode('utf-8')

            if DB.conn == None:
                await DB.connect()

            line_bot_fetch:List[dict] = await DB.select_rows(
                table_name='line_bot',
                columns=[],
                where_clause={}
            )

            for bot_info in line_bot_fetch:
                line_bot_secret:str = await decrypt_password(encrypted_password=bytes(bot_info.get('line_bot_secret')))
                # ハッシュ値を求める
                hash = hmac.new(
                    line_bot_secret.encode('utf-8'),
                    body.encode('utf-8'),
                    hashlib.sha256
                ).digest()

                # 結果を格納
                signature = base64.b64encode(hash)
                decode_signature = signature.decode('utf-8')

                line_bot_info = LineBotColunm(**bot_info)

                # ハッシュ値が一致した場合
                if decode_signature == x_line_signature:

                    guild_id:int = line_bot_info.guild_id
                    line_notify_token:str = await decrypt_password(encrypted_password=line_bot_info.line_notify_token)
                    line_bot_token:str = await decrypt_password(encrypted_password=line_bot_info.line_bot_token)

                    line_group_id:str = await decrypt_password(encrypted_password=line_bot_info.line_group_id)
                    default_channel_id:int = line_bot_info.default_channel_id

                    debug_mode:bool = line_bot_info.debug_mode
                    # Discordサーバーのインスタンスを作成
                    discord_find_message = ReqestDiscord(
                        guild_id=guild_id,
                        limit=int(EnvConf.USER_LIMIT),
                        token=TOKEN
                    )
                    # LINEのインスタンスを作成
                    line_bot_api = LineBotAPI(
                        notify_token=line_notify_token,
                        line_bot_token=line_bot_token,
                        line_group_id=line_group_id
                    )
                    # メッセージを送信するDiscordのテキストチャンネルのID
                    channel_id = default_channel_id
                    break

            # ハッシュ値が一致しなかった場合エラーを返す
            if decode_signature != x_line_signature:
                raise Exception

            # 応答確認の場合終了
            if type(response.events) is list:
                return HTMLResponse("OK")

            # デバッグモードがonの場合、LINEグループにグループidを返す
            if debug_mode:
                await line_bot_api.push_message_notify(message=f'本グループのグループid:{response.events.source.groupId}')

            # イベントの中身を取得
            event = response.events

            # LINEのプロフィールを取得(友達登録している場合)
            profile_name = await line_bot_api.get_proflie(user_id=event.source.userId)

            # テキストメッセージの場合
            if event.message.type == 'text':
                message = event.message.text
                # Discordのメンバー、ロール、チャンネルの指定があるか取得する
                """
                members_find
                テキストメッセージからユーザーのメンションを検出し、変換する。
                @ユーザー#0000#member → <@00000000000>

                roles_find
                テキストメッセージからロールのメンションを検出し、変換する。
                @ロール#role → <@&0000000000>

                channel_select
                テキストメッセージから送信場所を検出し、送信先のチャンネルidを返す。
                テキストチャンネルのみ送信可能。ただし、メッセージの先頭に書かれていなければ適用されない。
                /チャンネル名#channel → 削除
                """

                message = await discord_find_message.members_find(message=message)
                message = await discord_find_message.roles_find(message=message)
                channel_id, message = await discord_find_message.channel_select(
                    channel_id=channel_id,
                    message=message
                )

            # スタンプが送信された場合
            if event.message.type == 'sticker':
                # スタンプのurlを代入
                message = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{event.message.stickerId}/iPhone/sticker_key@2x.png"

            # 画像が送信された場合
            if event.message.type == 'image':
                # バイナリデータを取得しGyazoに送信
                fileobj = await line_bot_api.image_upload(event.message.id)
                await discord_find_message.send_discord_file(
                    channel_id=channel_id,
                    message=f'{profile_name.displayName}',
                    fileobj=fileobj
                )
                # レスポンス200を返し終了
                return HTMLResponse(content="OK")

            # 動画が送信された場合
            if event.message.type == 'video':
                # 動画をYouTubeにアップロードし、urlを返す
                youtube_id = await line_bot_api.movie_upload(
                    message_id=event.message.id,
                    display_name=profile_name.displayName
                )
                message = f"https://youtu.be/{youtube_id}"

            # 音声が送信された場合
            if event.message.type == 'audio':
                # 音声ファイルのデータを取得し、Discordに送信
                fileobj = await line_bot_api.voice_get(message_id=event.message.id)
                await discord_find_message.send_discord_file(
                    channel_id=channel_id,
                    message=f'{profile_name.displayName}',
                    fileobj=fileobj,
                    content_type='audio/mp4'
                )
                # レスポンス200を返し終了
                return HTMLResponse(content="OK")


            # LINEの名前 「メッセージ」の形式で送信
            message = f'{profile_name.displayName} \n「 {message} 」'
            await discord_find_message.send_discord(channel_id=channel_id, message=message)

            # レスポンス200を返し終了
            return HTMLResponse(content="OK")