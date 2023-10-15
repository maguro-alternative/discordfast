from discord import Guild

from pkg.db.database import PostgresDB

from typing import List,Dict
from core.auto_db_creator.bin.check_table import check_table_type

GUILD_SET_TABLE = 'guild_set_permissions'
GUILD_SET_COLUMNS = {
    'guild_id'                      : 'NUMERIC PRIMARY KEY',
    'line_permission'               : 'NUMERIC',
    'line_user_id_permission'       : 'NUMERIC[]',
    'line_role_id_permission'       : 'NUMERIC[]',
    'line_bot_permission'           : 'NUMERIC',
    'line_bot_user_id_permission'   : 'NUMERIC[]',
    'line_bot_role_id_permission'   : 'NUMERIC[]',
    'vc_permission'                 : 'NUMERIC',
    'vc_user_id_permission'         : 'NUMERIC[]',
    'vc_role_id_permission'         : 'NUMERIC[]',
    'webhook_permission'            : 'NUMERIC',
    'webhook_user_id_permission'    : 'NUMERIC[]',
    'webhook_role_id_permission'    : 'NUMERIC[]'
}
GUILD_SET_NEW_COLUMNS = {
    'guild_id'                      : 0,
    'line_permission'               : 8,
    'line_user_id_permission'       : [],
    'line_role_id_permission'       : [],
    'line_bot_permission'           : 8,
    'line_bot_user_id_permission'   : [],
    'line_bot_role_id_permission'   : [],
    'vc_permission'                 : 8,
    'vc_user_id_permission'         : [],
    'vc_role_id_permission'         : [],
    'webhook_permission'            : 8,
    'webhook_user_id_permission'    : [],
    'webhook_role_id_permission'    : []
}

async def guild_permissions_table_create(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    サーバーの権限を示すテーブルの作成、更新

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    if db.conn == None:
        await db.connect()
    # guildのテーブル
    table_name = f"{GUILD_SET_TABLE}"
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
                columns=GUILD_SET_COLUMNS
            )
            # 中身を空にする
            table_fetch = list()
        # テーブルがあって、中身もある場合
        else:
            # データベース側のカラムの型を入手
            table_columns_type = await db.get_columns_type(table_name=table_name)

            # テーブル内のカラムの型配列
            unchanged,table_fetch = await check_table_type(
                columns=GUILD_SET_COLUMNS,
                table_columns=table_columns_type,
                new_columns=GUILD_SET_NEW_COLUMNS,
                table_fetch=table_fetch
            )
            # テーブル内のカラム名配列
            guild_colums = [key for key in GUILD_SET_COLUMNS.keys()]
            table_colums = [key for key in table_columns_type.keys()]

            # テーブルの要素名か型が変更されていた場合、テーブルを削除し作成
            if set(table_colums) != set(guild_colums) or unchanged:
                table_fetch = await table_row_inheritance(
                    db=db,
                    table_name=table_name,
                    table_columns_type=table_columns_type
                )
                for row in table_fetch:
                    await db.insert_row(
                        table_name=table_name,
                        row_values=row
                    )

    # テーブルがあって、中身が空の場合
    if len(table_fetch) == 0:
        # データベース側のカラムの型を入手
        table_columns_type = await db.get_columns_type(table_name=table_name)

        # テーブル内のカラム名配列
        guild_colums = [key for key in GUILD_SET_COLUMNS.keys()]
        table_colums = [key for key in table_columns_type.keys()]
        # テーブルの要素名が変更されていた場合、テーブルを削除し作成
        if set(table_colums) != set(guild_colums):
            table_fetch = await table_row_inheritance(
                db=db,
                table_name=table_name,
                table_columns_type=table_columns_type
            )
        guild_new_colum = GUILD_SET_NEW_COLUMNS
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
        columns=GUILD_SET_COLUMNS,
        table_columns=table_columns_type,
        new_columns=GUILD_SET_NEW_COLUMNS,
        table_fetch=table_fetch
    )
    await db.drop_table(table_name=table_name)
    await db.create_table(
        table_name=table_name,
        columns=GUILD_SET_COLUMNS
    )

    return table_fetch