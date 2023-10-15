from typing import List,Dict

from discord import Guild

from pkg.db.database import PostgresDB

from core.auto_db_creator.bin.check_table import check_table_type

LINE_BOT_TABLE = 'line_bot'
LINE_BOT_COLUMNS = {
    'guild_id'          : 'NUMERIC PRIMARY KEY',
    'line_notify_token' : 'BYTEA',
    'line_bot_token'    : 'BYTEA',
    'line_bot_secret'   : 'BYTEA',
    'line_group_id'     : 'BYTEA',
    'line_client_id'    : 'BYTEA',
    'line_client_secret': 'BYTEA',
    'default_channel_id': 'NUMERIC',
    'debug_mode'        : 'BOOLEAN'
}
LINE_BOT_NEW_COLUMNS = {
    'guild_id'          : 0,
    'line_notify_token' : b'',
    'line_bot_token'    : b'',
    'line_bot_secret'   : b'',
    'line_group_id'     : b'',
    'line_client_id'    : b'',
    'line_client_secret': b'',
    'default_channel_id': 0,
    'debug_mode'        : False
}

async def line_bot_table_create(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    LINEからDiscordへの送信設定を示すテーブルの作成、更新

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """

    # テーブル名を代入
    table_name:str = LINE_BOT_TABLE

    if db.conn == None:
        await db.connect()

    table_fetch = await db.select_rows(
        table_name=table_name,
        columns=[],
        where_clause={
            'guild_id': guild.id
        }
    )

    if len(table_fetch) > 0:
        # テーブルがない場合作成
        if 'does not exist' in table_fetch[0]:
            await db.create_table(
                table_name=table_name,
                columns=LINE_BOT_COLUMNS
            )
            # 中身を空にする
            table_fetch = list()
        # テーブルがあって、中身もある場合
        else:
            # データベース側のカラムの型を入手
            table_columns_type = await db.get_columns_type(table_name=table_name)

            # テーブル内のカラムの型配列
            unchanged,table_fetch = await check_table_type(
                columns=LINE_BOT_COLUMNS,
                table_columns=table_columns_type,
                new_columns=LINE_BOT_NEW_COLUMNS,
                table_fetch=table_fetch
            )
            # テーブル内のカラム名配列
            guild_colums = [key for key in LINE_BOT_COLUMNS.keys()]
            table_colums = [key for key in table_columns_type.keys()]

            # テーブルの要素名か型が変更されていた場合、テーブルを削除し作成
            if table_colums != guild_colums or unchanged:
                table_fetch = await table_row_inheritance(
                    db=db,
                    table_name=table_name,
                    table_columns_type=table_columns_type
                )
                # まとめて作成(バッジ)
                await db.batch_insert_row(
                    table_name=table_name,
                    row_values=table_fetch
                )

    # テーブルがあって、中身が空の場合
    if len(table_fetch) == 0:
        # データベース側のカラムの型を入手
        table_columns_type = await db.get_columns_type(table_name=table_name)

        # テーブル内のカラム名配列
        guild_colums = [key for key in LINE_BOT_COLUMNS.keys()]
        table_colums = [key for key in table_columns_type.keys()]
        # テーブルの要素名が変更されていた場合、テーブルを削除し作成
        if set(table_colums) != set(guild_colums):
            table_fetch = await table_row_inheritance(
                db=db,
                table_name=table_name,
                table_columns_type=table_columns_type
            )

        guild_new_colum = LINE_BOT_NEW_COLUMNS
        guild_new_colum.update({
            'guild_id':guild.id
        })
        await db.insert_row(
            table_name=table_name,
            row_values=guild_new_colum
        )

async def table_row_inheritance(
    db:PostgresDB,
    table_name:str,
    table_columns_type:Dict
) -> List[Dict]:
    """
    カラム名、型が変更されていた場合、入っていた要素を保持しながら更新
    その後テーブルを削除し新たに作成

    Args:
        db (PostgresDB):
            データベースクラス
        table_name (str):
            テーブル名
        table_columns_type (Dict):
            データベース側の型

    Returns:
        List[Dict]:
            更新後のテーブルの中身
    """
    # テーブルすべての要素を取得(すべて削除されるのを防ぐため)
    table_fetch = await db.select_rows(
        table_name=table_name,
        columns=[],
        where_clause={}
    )
    # テーブル内のカラムの型配列
    unchanged,table_fetch = await check_table_type(
        columns=LINE_BOT_COLUMNS,
        table_columns=table_columns_type,
        new_columns=LINE_BOT_NEW_COLUMNS,
        table_fetch=table_fetch
    )
    await db.drop_table(table_name=table_name)
    await db.create_table(
        table_name=table_name,
        columns=LINE_BOT_COLUMNS
    )

    return table_fetch