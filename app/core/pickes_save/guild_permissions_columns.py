from discord import Guild

from base.database import PostgresDB
from base.aio_req import (
    pickle_write
)

from typing import List,Dict
from core.pickes_save.bin.check_table import check_table_type

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

async def guild_permissions_pickle_save(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    サーバーの権限を示すテーブルの作成、更新
    キャッシュデータの作成

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    # guildのテーブル
    table_name = f"{GUILD_SET_TABLE}"
    table_fetch = await db.select_rows(
        table_name=table_name,
        columns=[],
        where_clause={
            'guild_id': guild.id
        }
    )

    # データベース側のカラムの型を入手
    table_columns_type = await db.get_columns_type(table_name=table_name)

    # テーブル内のカラム名配列
    guild_colums = [key for key in GUILD_SET_COLUMNS.keys()]
    table_colums = [key for key in table_columns_type.keys()]

    # テーブル内のカラムの型配列
    unchanged,table_fetch = await check_table_type(
        columns=GUILD_SET_COLUMNS,
        table_columns=table_columns_type,
        new_columns=GUILD_SET_NEW_COLUMNS,
        table_fetch=table_fetch
    )

    # テーブルに変更があるかのフラグ
    changed_table_flag = table_colums != guild_colums or unchanged != False


    # テーブルをつくるか、カラムを取得するかのフラグ
    create_colum_flag = False
    create_table_flag = False

    # テーブルを削除するかのフラグ
    drop_table_flag = False

    if len(table_fetch) > 0:
        # テーブルが存在しない場合、作成
        if (table_fetch[0] == f"{table_name} does not exist"):
            create_table_flag = True
        # テーブルが存在する場合、カラムを格納
        else:
            create_colum_flag = True
    # テーブルが存在している
    elif len(table_fetch) == 0:
        print(f'テーブル:{table_name}の要素は空です')
        # 中身が空かつ、要素が変更されていた場合
        if changed_table_flag:
            drop_table_flag = True
        else:
            table_colums = [key for key in GUILD_SET_COLUMNS.keys()]

    # データベース側のカラムを格納
    if create_colum_flag:
        print(f'テーブル:{table_name}のカラム名一覧を作成します')
        table_colums = [key for key in table_fetch[0].keys()]

    # カラムの構成が変更されていた場合、削除し新たに作成する
    if changed_table_flag or drop_table_flag:
        print(f'テーブル:{table_name}を削除します')
        create_table_flag = True
        await db.drop_table(table_name=table_name)

    # テーブルの作成
    if create_table_flag:
        print(f'テーブル:{table_name}を作成します')
        await db.create_table(
            table_name=table_name,
            columns=GUILD_SET_COLUMNS
        )

    # テーブルに変更があった場合
    if changed_table_flag and len(table_fetch) != 0:
        if "does not exist" not in table_fetch[0]:
            # まとめて作成(バッジ)
            await db.batch_insert_row(
                table_name=table_name,
                row_values=table_fetch
            )

    # ない場合は新規で登録
    if len(table_fetch) == 0 or create_table_flag:
        guild_new_colum = GUILD_SET_NEW_COLUMNS
        guild_new_colum.update({
            'guild_id':guild.id
        })
        await db.insert_row(
            table_name=table_name,
            row_values=guild_new_colum
        )

    # テーブルの要素を取得
    table_fetch = await db.select_rows(
        table_name=table_name,
        columns=[],
        where_clause={}
    )

    print(f'{table_name}.pickleの書き込みをはじめます')

    # pickleファイルに書き込み
    await pickle_write(
        filename=table_name,
        table_fetch=table_fetch
    )

    print(f'{table_name}.pickleの書き込みが終了しました')


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
        if 'does not exist' in table_fetch:
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
        guild_colums = [key for key in GUILD_SET_COLUMNS.keys()]
        table_colums = [key for key in table_columns_type.keys()]
        # テーブルの要素名が変更されていた場合、テーブルを削除し作成
        if table_colums != guild_colums:
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