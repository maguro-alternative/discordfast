from discord import Guild

from pkg.db.database import PostgresDB

from typing import List,Dict

from core.auto_db_creator.bin.check_table import check_table_type

WEBHOOK_TABLE = 'webhook_set'
WEBHOOK_COLUMNS = {
    'uuid'              : 'UUID PRIMARY KEY',
    'guild_id'          : 'NUMERIC',
    'webhook_id'        : 'NUMERIC',
    'subscription_type' : 'VARCHAR(50)',
    'subscription_id'   : 'VARCHAR(50)',
    'mention_roles'     : 'NUMERIC[]',
    'mention_members'   : 'NUMERIC[]',
    'ng_or_word'        : 'VARCHAR(50)[]',
    'ng_and_word'       : 'VARCHAR(50)[]',
    'search_or_word'    : 'VARCHAR(50)[]',
    'search_and_word'   : 'VARCHAR(50)[]',
    'mention_or_word'   : 'VARCHAR(50)[]',
    'mention_and_word'  : 'VARCHAR(50)[]',
    'created_at'        : 'VARCHAR(50)'
}
WEBHOOK_NEW_COLUMNS = {
    'uuid'              : '',
    'guild_id'          : 0,
    'webhook_id'        : 0,
    'subscription_type' : '',
    'subscription_id'   : '',
    'mention_roles'     : [],
    'mention_members'   : [],
    'ng_or_word'        : [],
    'ng_and_word'       : [],
    'search_or_word'    : [],
    'search_and_word'   : [],
    'mention_or_word'   : [],
    'mention_and_word'  : [],
    'created_at'        : ''
}

async def webhook_pickle_table_create(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    webhook設定のテーブルの作成、更新

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    # Webhookのテーブル
    table_name = WEBHOOK_TABLE

    if db.conn == None:
        await db.connect()

    table_fetch:List[Dict] = await db.select_rows(
        table_name=table_name,
        columns=[],
        where_clause={
            'guild_id':guild.id
        }
    )

    if len(table_fetch) > 0:
        # テーブルがない場合作成
        if 'does not exist' in table_fetch[0]:
            await db.create_table(
                table_name=table_name,
                columns=WEBHOOK_COLUMNS
            )
            # 中身を空にする
            table_fetch = list()
        # テーブルがあって、中身もある場合
        else:
            # データベース側のカラムの型を入手
            table_columns_type = await db.get_columns_type(table_name=table_name)

            # テーブル内のカラムの型配列
            unchanged,table_fetch = await check_table_type(
                columns=WEBHOOK_COLUMNS,
                table_columns=table_columns_type,
                new_columns=WEBHOOK_NEW_COLUMNS,
                table_fetch=table_fetch
            )
            # テーブル内のカラム名配列
            guild_colums = [key for key in WEBHOOK_COLUMNS.keys()]
            table_colums = [key for key in table_columns_type.keys()]

            # テーブルの要素名か型が変更されていた場合、テーブルを削除し作成
            if set(table_colums) != set(guild_colums) or unchanged:
                await db.drop_table(table_name=table_name)
                await db.create_table(
                    table_name=table_name,
                    columns=WEBHOOK_COLUMNS
                )
                for row in table_fetch:
                    await db.insert_row(
                        table_name=table_name,
                        row=row
                    )