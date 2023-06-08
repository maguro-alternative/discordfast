from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
load_dotenv()

from cryptography.fernet import Fernet
from itertools import groupby,chain

import os
from typing import List,Dict

from base.aio_req import (
    aio_get_request,
    pickle_read
)

LINE_OAUTH_BASE_URL = "https://api.line.me/oauth2/v2.1"
LINE_BOT_URL = 'https://api.line.me/v2/bot'

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

ENCRYPTED_KEY = os.environ["ENCRYPTED_KEY"]

router = APIRouter()

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

@router.get('/group/{guild_id}')
async def group(
    request:Request,
    guild_id:int
):
    # OAuth2トークンが有効かどうか判断
    if request.session.get('line_oauth_data'):
        try:
            oauth_session = await aio_get_request(
                url=f"{LINE_OAUTH_BASE_URL}/verify?access_token={request.session['line_oauth_data']['access_token']}",
                headers={}
            )
            # トークンの有効期限が切れていた場合、再ログインする
            if oauth_session.get('error_description') == 'Invalid IdToken Nonce.':
                return RedirectResponse(url='/line-login')
        except KeyError:
            return RedirectResponse(url='/line-login')
    else:
        return RedirectResponse(url='/line-login')
    
    line_bot_table:List[Dict] = await pickle_read(filename="line_bot")

    guild_id = request.session.get('guild_id')

    guild_set_line_bot:List[Dict] = [
        line
        for line in line_bot_table
        if int(line.get('guild_id')) == int(guild_id)
    ]

    line_group_id:str = await decrypt_password(encrypted_password=bytes(guild_set_line_bot[0].get('line_group_id')))
    line_bot_token:str = await decrypt_password(encrypted_password=bytes(guild_set_line_bot[0].get('line_bot_token')))

    default_channel_id:int = int(guild_set_line_bot[0].get('default_channel_id'))

    # グループIDが有効かどうか判断
    r = await aio_get_request(
        url=f"{LINE_BOT_URL}/group/{line_group_id}/member/{request.session['line_user']['sub']}",
        headers={
            'Authorization': f'Bearer {line_bot_token}'
        }
    )
    # グループIDが無効の場合、友達から判断
    if r.get('message') != None:
        raise HTTPException(status_code=400, detail="認証失敗")

    # サーバのチャンネル一覧を取得
    all_channel = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # ソート後のチャンネル一覧
    all_channel_sort = await sort_discord_channel(all_channel=all_channel)


    return templates.TemplateResponse(
        "linegroup.html",
        {
            "request": request, 
            "guild_id": guild_id,
            "all_channel": all_channel_sort,
            "default_channel_id":default_channel_id,
            "title":f"{request.session['line_user']['name']}のサーバ一覧"
        }
    )

# 復号化関数
async def decrypt_password(encrypted_password:bytes) -> str:
    cipher_suite = Fernet(ENCRYPTED_KEY)
    try:
        decrypted_password = cipher_suite.decrypt(encrypted_password)
        return decrypted_password.decode('utf-8')
    # トークンが無効の場合
    except:
        return ''
    
async def sort_discord_channel(
    all_channel:List
) -> List:
     # 親カテゴリー格納用
    position = []

    # レスポンスのJSONからpositionでソートされたリストを作成
    sorted_channels = sorted(all_channel, key=lambda c: c['position'])

    # parent_idごとにチャンネルをまとめた辞書を作成
    channel_dict = {}

    for parent_id, group in groupby(
        sorted_channels, 
        key=lambda c: c['parent_id']
    ):
        if parent_id is None:
            # 親カテゴリーのないチャンネルは、キーがNoneの辞書に追加される
            parent_id = 'None'
    
        # キーがまだない場合、作成(同時に値も代入)
        if channel_dict.get(str(parent_id)) == None:
            channel_dict[str(parent_id)] = list(group)
        # キーがある場合、リストを取り出して結合し代入
        else:
            listtmp:List = channel_dict[str(parent_id)]
            listtmp.extend(list(group))
            channel_dict[str(parent_id)] = listtmp
            # リストを空にする
            listtmp = list()

    # 親カテゴリーがある場合、Noneから取り出す
    for chan in channel_dict['None'][:]:
        if chan['type'] == 4:
            position.append(chan)
            channel_dict['None'].remove(chan)

    # 辞書を表示
    position_index = 0

    # 親カテゴリーの名前をリスト化
    extracted_list = [d["name"] for d in position]
    # カテゴリーに属しないチャンネルが存在する場合
    if len(channel_dict['None']) != 0:
        # 配列の長さをカテゴリー数+1にする
        all_channels = [{}] * (len(extracted_list) + 1)
    else:
        all_channels = [{}] * len(extracted_list)

    for parent_id, channel in channel_dict.items():
        # カテゴリー内にチャンネルがある場合
        if len(channel) != 0:
            for d in position:
                # カテゴリーを探索、あった場合positionを代入
                if d['id'] == channel[0]['parent_id']:
                    position_index = d['position']
                    break
        else:
            position_index = len(extracted_list)
    
        if len(channel) != 0:
            # 指定したリストの中身が空でない場合、空のリストを探す
            while len(all_channels[position_index]) != 0:
                if len(extracted_list) == position_index:
                    position_index -= 1
                else:
                    position_index += 1

            # 指定した位置にカテゴリー内のチャンネルを代入
            all_channels[position_index] = channel

            # 先頭がカテゴリーでない場合
            if channel[0]['parent_id'] != None:
                # 先頭にカテゴリーチャンネルを代入
                all_channels[position_index].insert(0,d)
    
    # list(list),[[],[]]を一つのリストにする
    all_channel_sort = list(chain.from_iterable(all_channels))

    return all_channel_sort