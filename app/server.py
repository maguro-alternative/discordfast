from fastapi import FastAPI,HTTPException,Request,Header,Response
from fastapi.responses import HTMLResponse
from threading import Thread
import uvicorn

import json

import base64
import hashlib
import hmac

from dotenv import load_dotenv
load_dotenv()

try:
    from message_type.line_type.class_type import Profile,EventResponse
    from message_type.line_type.line_event import Line_Responses
    from message_type.discord_type.message_creater import MessageFind
    from message_type.line_type.line_message import Notify
except:
    from app.message_type.line_type.class_type import Profile,EventResponse
    from app.message_type.line_type.line_event import Line_Responses
    from app.message_type.discord_type.message_creater import MessageFind
    from app.message_type.line_type.line_message import Notify
# ./venv/Scripts/activate.bat

import os

bots_name = os.environ['BOTS_NAME'].split(",")
TOKEN = os.environ['TOKEN']

app = FastAPI()

# x_line_signature:str=Header(None)

# LINE側のメッセージを受け取る
@app.post("/line_bot")
async def line_response(
    response:Line_Responses,
    byte_body:Request, 
    x_line_signature=Header(None)
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
    
    # destination(BotのID)からbotの種類を判別する
    for bot_name in bots_name:
        if response.destination == os.environ[f'{bot_name}_BOTS_DESTINATION']:
            channel_secret = os.environ[f'{bot_name}_CHANNEL_SECLET']
            # Discordサーバーのクラスを宣言
            discord_find_message = MessageFind(int(os.environ[f'{bot_name}_GUILD_ID']), 100, TOKEN)
            # LINEのクラスを宣言
            line_bot_api = Notify(
                notify_token=os.environ.get(f'{bot_name}_NOTIFY_TOKEN'),
                line_bot_token=os.environ[f'{bot_name}_BOTS_TOKEN'],
                line_group_id=os.environ.get(f'{bot_name}_GROUP_ID')
            )
            # メッセージを送信するDiscordのテキストチャンネルのID
            channel_id = int(os.environ[f'{bot_name}_CHANNEL_ID'])
            break

    # request.bodyを取得
    boo = await byte_body.body()
    body = boo.decode('utf-8')
    
    # ハッシュ値を求める
    hash = hmac.new(
        channel_secret.encode('utf-8'),
        body.encode('utf-8'), 
        hashlib.sha256
    ).digest()

    # 結果を格納
    signature = base64.b64encode(hash)

    decode_signature = signature.decode('utf-8')

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
        # Disocrdのメンバー、ロール、チャンネルの指定があるか取得する
        """
        以下の文字がメッセージに含まれていた場合、変換を行う
        @メンバー名#member
        @ロール名#role
        /テキストチャンネル名#channel(テキストの先頭にあった場合)
        diecord_request:List[tuple] = [
            (@メンバー名#member,                   <@メンバーid>),
            (@ロール名#role,                       <@&ロールid>),
            (/テキストチャンネル名#channel,         テキストチャンネルid)
        ]
        該当するものがない場合、Noneを返す。
        """
        discord_request = [await discord_find_message.member_find(message),
                            await discord_find_message.role_find(message),
                            await discord_find_message.channel_find(message)]

        # Discordへリクエストした内容を展開
        for req_find in discord_request:
            # 該当するものがあった場合
            if req_find != None:
                # テキストチャンネルidの場合
                if type(req_find[1]) is int:
                    # /テキストチャンネル名#channelを削除し、テキストチャンネルidを代入
                    message = message.lstrip(req_find[0])
                    channel_id = req_find[1]
                else:
                    # メンション形式に変換
                    message = message.replace(req_find[0], req_find[1])

    # スタンプが送信された場合
    if event.message.type == 'sticker':
        # スタンプのurlを代入
        message = f"https://stickershop.line-scdn.net/stickershop/v1/sticker/{event.message.stickerId}/iPhone/sticker_key@2x.png"

    # 画像が送信された場合
    if event.message.type == 'image':
        # バイナリデータを取得しGyazoに送信
        gyazo_json = await line_bot_api.get_image_byte(event.message.id)
        # Gyazoのurlを返す
        message = f"https://i.gyazo.com/{gyazo_json.image_id}.{gyazo_json.type}"

    # 動画が送信された場合
    if event.message.type == 'video':
        # 動画をYouTubeにアップロードし、urlを返す
        message = await line_bot_api.movie_upload(message_id=event.message.id,display_name=profile_name.display_name)

    # LINEの名前 「メッセージ」の形式で送信
    message = f'{profile_name.display_name} \n「 {message} 」'
    await discord_find_message.send_discord(channel_id=channel_id, message=message)

    return HTMLResponse(content="OK")

@app.post("/line_bot/success")
async def read_root(response:Request, x_line_signature=Header(None)):
    #r = response.json()
    #res = await r
    #print(res)
    #body = await response.body()
    #print(type(re))
    #print(response.headers)
    
    boo = await response.body()
    body = boo.decode('utf-8')
    
    hash = hmac.new(
        os.environ[f'6_CHANNEL_SECLET'].encode('utf-8'),
        body.encode('utf-8'), 
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(hash)

    b = signature.decode('utf-8')
    print(boo)

    print(b)
    

    print(x_line_signature)

    return {"Hello": "World"}

@app.get("/")
async def read_root(response):
    r = response
    print(r)
    return {"Hello": "World"}

def run():
    uvicorn.run(app, port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == '__main__':
    uvicorn.run(app,host='localhost', port=8000)