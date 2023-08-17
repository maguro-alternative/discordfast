from discord import Guild

from dotenv import load_dotenv
load_dotenv()

from typing import List
import os

from base.database import PostgresDB


from core.pickes_save import (
    line_columns,
    vc_columns,
    webhook_columns,
    guild_permissions_columns,
    line_bot_columns
)
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

async def db_pickle_save(guilds:List[Guild]) -> None:
    """
    データベースのテーブルの中身をキャッシュデータとしてローカルに保存します。

    param:
    guilds  :List[discord.Guild]
    Botが所属しているDiscordサーバのクラス
    """
    # データベースへ接続
    if db.conn == None:
        await db.connect()
    # サーバごとにテーブルのキャッシュデータを作成
    for guild in guilds:
        #await line_columns.line_pickle_save(db=db,guild=guild)
        #await vc_columns.vc_pickle_save(db=db,guild=guild)
        #await webhook_columns.webhook_pickle_save(db=db,guild=guild)
        #await guild_permissions_columns.guild_permissions_pickle_save(db=db,guild=guild)
        #await line_bot_columns.line_bot_pickle_save(db=db,guild=guild)

        await line_columns.line_pickle_table_create(db=db,guild=guild)
        await vc_columns.vc_pickle_table_create(db=db,guild=guild)
        await webhook_columns.webhook_pickle_table_create(db=db,guild=guild)
        await guild_permissions_columns.guild_permissions_table_create(db=db,guild=guild)
        await line_bot_columns.line_bot_table_create(db=db,guild=guild)


    #await db.disconnect()
