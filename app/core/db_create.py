from discord import Guild

from typing import List

from pkg.db.database import PostgresDB
from core.auto_db_creator import (
    line_columns,
    vc_columns,
    webhook_columns,
    guild_permissions_columns,
    line_bot_columns
)
from model_types.environ_conf import EnvConf
DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

USER = EnvConf.PGUSER
PASSWORD = EnvConf.PGPASSWORD
DATABASE = EnvConf.PGDATABASE
HOST = EnvConf.PGHOST
DB = PostgresDB(
    user=USER,
    password=PASSWORD,
    database=DATABASE,
    host=HOST
)

async def db_auto_creator(guilds:List[Guild]) -> None:
    """
    データベースのテーブルの中身をキャッシュデータとしてローカルに保存します。

    param:
    guilds  :List[discord.Guild]
    Botが所属しているDiscordサーバのクラス
    """
    # データベースへ接続
    if DB.conn == None:
        await DB.connect()
    # サーバごとにテーブルのキャッシュデータを作成
    for guild in guilds:
        await line_columns.line_pickle_table_create(db=DB,guild=guild)
        await vc_columns.vc_pickle_table_create(db=DB,guild=guild)
        await webhook_columns.webhook_pickle_table_create(db=DB,guild=guild)
        await guild_permissions_columns.guild_permissions_table_create(db=DB,guild=guild)
        await line_bot_columns.line_bot_table_create(db=DB,guild=guild)
