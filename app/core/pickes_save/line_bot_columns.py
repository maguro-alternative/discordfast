from typing import List,Dict

from discord import Guild

from base.database import PostgresDB
from base.aio_req import (
    pickle_write
)

from core.pickes_save.bin.check_table import check_table_type

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

async def line_bot_pickle_save(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    LINEからDiscordへの送信設定を示すテーブルの作成、更新
    キャッシュデータの作成

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """

    # テーブル名を代入
    table_name:str = LINE_BOT_TABLE

    # テーブルをつくるか、カラムを取得するかのフラグ
    create_colum_flag = False
    create_table_flag = False

    # テーブルを削除するかのフラグ
    drop_table_flag = False

    # テーブルの要素を取得
    table_fetch:List[Dict] = await db.select_rows(
        table_name=f"{table_name}",
        columns=[],
        where_clause={
            'guild_id': guild.id
        }
    )

    # テーブル内のカラム名配列
    channel_colums = [key for key in LINE_BOT_COLUMNS.keys()]

    #print(table_columns_type)

    table_columns_type = await db.get_columns_type(table_name=table_name)

    if len(table_columns_type) == 0:
        # テーブル未作成の場合、同じ型を宣言
        if (table_fetch[0] == f"{table_name} does not exist"):
            table_colums = [key for key in LINE_BOT_COLUMNS.keys()]
        else:
            # データベース側のカラムの型を入手
            table_colums = [key for key in table_columns_type.keys()]
    else:
        # データベース側のカラムの型を入手
        table_colums = [key for key in table_columns_type.keys()]

    # print(table_fetch)

    # テーブルの方が存在する場合
    if bool('table_columns_type' in locals()):
        # テーブル内のカラムの型配列
        unchanged,table_fetch = await check_table_type(
            columns=LINE_BOT_COLUMNS,
            table_columns=table_columns_type,
            new_columns=LINE_BOT_NEW_COLUMNS,
            table_fetch=table_fetch
        )
    else:
        unchanged = False

    # テーブルに変更があるかのフラグ
    changed_table_flag = table_colums != channel_colums or unchanged != False

    # テーブルがなかった場合、作成
    if len(table_fetch) > 0:
        # テーブルが存在しない場合、作成
        if (table_fetch[0] == f"{table_name} does not exist"):
            create_table_flag = True
        # テーブルが存在する場合、カラムを格納
        else:
            create_colum_flag = True

    # テーブルが存在しているが、中身が空
    elif len(table_fetch) == 0:
        print(f'テーブル:{table_name}の{guild.id}の要素は空です')
        # 要素が変更されていた場合
        if changed_table_flag:
            drop_table_flag = True
        # ローカル側のカラムを格納
        else:
            table_colums = [key for key in LINE_BOT_COLUMNS.keys()]

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
            columns=LINE_BOT_COLUMNS
        )

    # テーブルに変更があった場合
    if changed_table_flag and len(table_fetch) != 0:
        if "does not exist" not in table_fetch[0]:
            # まとめて作成(バッジ)
            await db.insert_row(
                table_name=table_name,
                row_values=table_fetch[0]
            )

    # 中身が空の場合
    if len(table_fetch) == 0 or create_table_flag:

        row_values = []

        row = {}
        for key,values in LINE_BOT_NEW_COLUMNS.items():
            # 各要素を更新
            if key == "guild_id":
                value = guild.id
            elif key == "default_channel_id":
                # システムチャンネルがある場合代入
                if hasattr(guild.system_channel,'id'):
                    value = guild.system_channel.id
            else:
                value = values
            row.update({key:value})

        row_values.append(row)

        # 一つ一つ作成
        await db.insert_row(
            table_name=table_name,
            row_values=row
        )

    # テーブルの要素を取得
    table_fetch:List[Dict] = await db.select_rows(
        table_name=f"{table_name}",
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
        if 'does not exist' in table_fetch:
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
        if table_colums != guild_colums:
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