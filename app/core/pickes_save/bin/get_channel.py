from base.aio_req import (
    aio_get_request
)

from dotenv import load_dotenv
load_dotenv()


import os
from typing import List,Dict,Any
DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

async def get_discord_channel(
    guild_id:int,
    get_channel_type:List[int]
) -> List[Dict[str,Any]]:
    """
    Discordサーバ内のチャンネルを取得します。

    param:
    guild_id            :int
    Discordのサーバid

    get_channel_type    :List[int]
    取得するチャンネルtype
    空の場合、すべて取得する
    以下に説明を記す


    0:テキストチャンネル	
        Discordサーバのテキストチャンネル
    1:ダイレクトメッセージ	
        一ユーザへのダイレクトメッセージ
    2:ボイスチャンネル	
        Discordサーバのボイスチャンネル
    3:グループダイレクトメッセージ	
        複数のユーザから構成されるダイレクトメッセージ
    4:カテゴリーチャンネル	
        テキストチャンネルやボイスチャンネルをまとめる親チャンネル
    5:ギルドアナウンスチャンネル(旧ニュースチャンネル)	
        お気に入りにしたサーバの通知や、Discord公式の通知を受け取るチャンネル
    10:アナウンスチャンネル	
        5で作成されるスレッドチャンネル
    11:公開スレッドチャンネル	
        0で作成されるスレッドチャンネル
        公開に設定されている場合はこちら
    12:非公開スレッドチャンネル	
        0で作成されるスレッドチャンネル
        非公開に設定されている場合はこちら
    13:ステージチャンネル	
        ラジオのような聞き専のチャンネル
    14:ギルドディレクトリチャンネル	
        サーバ紹介をするチャンネル
        大規模なコミュニティサーバでのみ使用可能
        以下のリンクに使用例あり
        https://support.discord.com/hc/ja/articles/4406046651927-DIscord%E5%AD%A6%E7%94%9F%E3%83%8F%E3%83%96FAQ#:~:text=Discord%E5%AD%A6%E7%94%9F%E3%83%8F%E3%83%96%E3%81%AF%E3%80%81%E5%AD%A6%E7%94%9F,%E3%81%99%E3%82%8B%E3%81%93%E3%81%A8%E3%81%8C%E3%81%A7%E3%81%8D%E3%81%BE%E3%81%99%E3%80%82
    15:フォーラムチャンネル	
        特定の話題について議論するチャンネル
    """
    # サーバのチャンネル一覧を取得
    all_channel = await aio_get_request(
        url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
        }
    )

    # 空の場合、すべてのチャンネルを格納
    if len(get_channel_type) == 0:
        all_channel_filter = [
            channel
            for channel in all_channel
        ]
    else:
        # 該当するチャンネルだけ格納
        all_channel_filter = [
            channel
            for channel in all_channel
            if channel['type'] in get_channel_type
        ]

    return all_channel_filter