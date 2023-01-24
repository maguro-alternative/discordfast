from fastapi import FastAPI,Depends,HTTPException,Request,Header,Response
from fastapi.responses import HTMLResponse
#from fastapi.security import OAuth2PasswordBearer
from threading import Thread
import uvicorn


#from passlib.context import CryptContext

import base64
import hashlib
import hmac
import re

from dotenv import load_dotenv
load_dotenv()

try:
    from message_type.line_type.line_event import Line_Responses
    from message_type.discord_type.message_creater import ReqestDiscord
    from message_type.line_type.line_message import LineBotAPI
except:
    from app.message_type.line_type.line_event import Line_Responses
    from app.message_type.discord_type.message_creater import ReqestDiscord
    from app.message_type.line_type.line_message import LineBotAPI
# ./venv/Scripts/activate.bat

import os

bots_name = os.environ['BOTS_NAME'].split(",")
TOKEN = os.environ['TOKEN']

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# x_line_signature:str=Header(None)

# LINE側のメッセージを受け取る
@app.post("/line_bot")
async def line_response(
    response:Line_Responses,
    byte_body:Request, 
    x_line_signature=Header(None),
    #token: str = Depends(oauth2_scheme)
):
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

    # channel_secretからbotの種類を判別する
    for bot_name in bots_name:
        channel_secret = os.environ[f'{bot_name}_CHANNEL_SECRET']
        # ハッシュ値を求める
        hash = hmac.new(
            channel_secret.encode('utf-8'),
            body.encode('utf-8'), 
            hashlib.sha256
        ).digest()

        # 結果を格納
        signature = base64.b64encode(hash)
        decode_signature = signature.decode('utf-8')

        if decode_signature == x_line_signature:
            channel_secret = os.environ[f'{bot_name}_CHANNEL_SECRET']
            # Discordサーバーのクラスを宣言
            discord_find_message = ReqestDiscord(
                guild_id = int(os.environ[f'{bot_name}_GUILD_ID']),
                limit = int(os.environ["USER_LIMIT"]), 
                token = TOKEN
            )
            # LINEのクラスを宣言
            line_bot_api = LineBotAPI(
                notify_token = os.environ.get(f'{bot_name}_NOTIFY_TOKEN'),
                line_bot_token = os.environ[f'{bot_name}_BOT_TOKEN'],
                line_group_id = os.environ.get(f'{bot_name}_GROUP_ID')
            )
            # メッセージを送信するDiscordのテキストチャンネルのID
            channel_id = int(os.environ[f'{bot_name}_CHANNEL_ID'])
            break

    # ハッシュ値が一致しなかった場合エラーを返す
    if decode_signature != x_line_signature: 
        raise Exception

    # 応答確認の場合終了
    if type(response.events) is list:
        return HTMLResponse("OK")

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

        member_mention_list = re.findall("@.*?#\d*?#member",message,re.S)

        if member_mention_list:
            get_member_list = await discord_find_message.member_get()

            for member in get_member_list:
                # メッセージに「@{ユーザー名}#{4桁の数字}member」が含まれていた場合
                if f'@{member.user.username}#{member.user.discreminator}#member' in member_mention_list:
                    message = message.replace(f'@{member.user.username}#{member.user.discreminator}#member',f'<@{member.user.id}>')
                    member_mention_list.remove(f'@{member.user.username}#{member.user.discreminator}#member')
                if not member_mention_list:
                    break

        role_list = re.findall("@.*?#role",message,re.S)

        if role_list:
            get_role_list = await discord_find_message.role_get()

            for role in get_role_list:
                # メッセージに「@{ロール名}#role」が含まれていた場合
                if f'@{role.name}#role' in role_list:
                    message = message.replace(f'@{role.name}#role',f'<@&{role.id}>')
                    role_list.remove(f'@{role.name}#role')
                if not role_list:
                    break

        channel_list = re.findall("\A/.*?#channel",message,re.S)

        if channel_list and message.find('/') == 0:
            get_channel_list = await discord_find_message.channel_get()

            for channel in get_channel_list:
                # メッセージの先頭に「/{チャンネル名}#channel」が含まれていた場合
                if message.find(f'/{channel.name}#channel') == 0 and channel.type == 0:
                    message = message.lstrip(f'/{channel.name}#channel')
                    channel_id = channel.id
                    break
        
        #message = await discord_find_message.members_find(message=message)
        #message = await discord_find_message.roles_find(message=message)
        #channel_id ,message = await discord_find_message.channel_select(channel_id=channel_id,message=message)

    # スタンプが送信された場合
    if event.message.type == 'sticker':
        # スタンプのurlを代入
        message = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{event.message.stickerId}/iPhone/sticker_key@2x.png"

    # 画像が送信された場合
    if event.message.type == 'image':
        # バイナリデータを取得しGyazoに送信
        gyazo_json = await line_bot_api.image_upload(event.message.id)
        # Gyazoのurlを返す
        message = f"https://i.gyazo.com/{gyazo_json.image_id}.{gyazo_json.type}"

    # 動画が送信された場合
    if event.message.type == 'video':
        # 動画をYouTubeにアップロードし、urlを返す
        message = await line_bot_api.movie_upload(message_id=event.message.id,display_name=profile_name.display_name)
        # 容量を確保するために、動画を削除
        os.remove(f'.\movies\{event.message.id}.mp4')

    # LINEの名前 「メッセージ」の形式で送信
    message = f'{profile_name.display_name} \n「 {message} 」'
    await discord_find_message.send_discord(channel_id=channel_id, message=message)

    # レスポンス200を返し終了
    return HTMLResponse(content="OK")

def run():
    uvicorn.run("server:app",  host="0.0.0.0", port=int(os.getenv("PORT", default=5000)), log_level="info")

# DiscordBotと並列で立ち上げる
def keep_alive():
    t = Thread(target=run)
    t.start()

# ローカルで実行する際
if __name__ == '__main__':
    uvicorn.run(app,host='localhost', port=8000)