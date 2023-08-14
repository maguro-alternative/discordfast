from typing import List,Dict

from discord import Guild

from base.database import PostgresDB
from base.aio_req import (
    pickle_write
)

from core.pickes_save.bin.get_channel import get_discord_channel
from core.pickes_save.bin.check_table import check_table_type

LINE_TABLE = 'guilds_line_channel_'
LINE_COLUMNS = {
    'channel_id'        : 'NUMERIC PRIMARY KEY',
    'guild_id'          : 'NUMERIC',
    'line_ng_channel'   : 'boolean',
    'ng_message_type'   : 'VARCHAR(50)[]',
    'message_bot'       : 'boolean',
    'ng_users'          : 'NUMERIC[]'
}
LINE_NEW_COLUMNS = {
    'channel_id'        : 0,
    'guild_id'          : 0,
    'line_ng_channel'   : False,
    'ng_message_type'   : [],
    'message_bot'       : True,
    'ng_users'          : []
}
# 取得するチャンネルのタイプ
LINE_TYPE = [0,2]

async def line_pickle_save(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    LINEへの送信設定を示すテーブルの作成、更新
    キャッシュデータの作成

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    # テーブル名を代入
    table_name:str = f"{LINE_TABLE}{guild.id}"

    # テーブルをつくるか、カラムを取得するかのフラグ
    create_colum_flag = False
    create_table_flag = False

    # テーブルを削除するかのフラグ
    drop_table_flag = False

    # テーブルの要素を取得
    table_fetch:List[Dict] = await db.select_rows(
        table_name=f"{table_name}",
        columns=[],
        where_clause={}
    )

    # テーブル内のカラム名配列
    channel_colums = [key for key in LINE_COLUMNS.keys()]

    # テーブルがなかった場合、作成
    if len(table_fetch) > 0:
        # テーブルが存在しない場合、作成
        if (table_fetch[0] == f"{table_name} does not exist"):
            create_table_flag = True
            table_colums = [key for key in LINE_COLUMNS.keys()]
        # テーブルが存在する場合、カラムを格納
        else:
            create_colum_flag = True
            # データベース側のカラムの型を入手
            table_columns_type = await db.get_columns_type(table_name=table_name)
            table_colums = [key for key in table_columns_type.keys()]
    else:
        # データベース側のカラムの型を入手
        table_columns_type = await db.get_columns_type(table_name=table_name)
        table_colums = [key for key in table_columns_type.keys()]

    # print(table_fetch)

    # テーブルの方が存在する場合
    if bool('table_columns_type' in locals()):
        # テーブル内のカラムの型配列
        unchanged,table_fetch = await check_table_type(
            columns=LINE_COLUMNS,
            table_columns=table_columns_type,
            new_columns=LINE_NEW_COLUMNS,
            table_fetch=table_fetch
        )
    else:
        unchanged = False

    # テーブルに変更があるかのフラグ
    changed_table_flag = table_colums != channel_colums or unchanged != False

    # テーブルが存在しているが、中身が空
    if len(table_fetch) == 0:
        print(f'テーブル:{table_name}の要素は空です')
        # 要素が変更されていた場合
        if changed_table_flag:
            drop_table_flag = True
        # ローカル側のカラムを格納
        else:
            table_colums = [key for key in LINE_COLUMNS.keys()]

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
            columns=LINE_COLUMNS
        )

    # テーブルに変更があった場合
    if changed_table_flag and len(table_fetch) != 0:
        # まとめて作成(バッジ)
        await db.batch_insert_row(
            table_name=table_name,
            row_values=table_fetch
        )

        # テーブルの要素を取得
        table_fetch:List[Dict] = await db.select_rows(
            table_name=f"{table_name}",
            columns=[],
            where_clause={}
        )

    # 中身が空の場合
    elif len(table_fetch) == 0 or (create_table_flag != changed_table_flag):

        # Discordのチャンネルを取得
        all_channel = await get_discord_channel(
            guild_id=guild.id,
            get_channel_type=LINE_TYPE
        )

        row_values = []

        for channel in all_channel:
            row = {}
            for key,values in LINE_NEW_COLUMNS.items():
                # 各要素を更新
                if key == "channel_id":
                    value = channel["id"]
                elif key == "guild_id":
                    value = guild.id
                elif key == "send_channel_id":
                    # システムチャンネルがある場合代入
                    if hasattr(guild.system_channel,'id'):
                        value = guild.system_channel.id
                    # 設定されていない場合、0を代入
                    else:
                        value = 0
                else:
                    value = values
                row.update({key:value})

            row_values.append(row)
            # print(row)

            # 一つ一つ作成
            # await db.insert_row(table_name=table_name,row_values=row)

        # まとめて作成(バッジ)
        await db.batch_insert_row(
            table_name=table_name,
            row_values=row_values
        )

        # テーブルの要素を取得
        table_fetch:List[Dict] = await db.select_rows(
            table_name=f"{table_name}",
            columns=[],
            where_clause={}
        )

    dict_row = list()
    #print(table_fetch)

    # テーブルに中身がある場合
    if len(table_fetch) > 0:
        if table_fetch[0] != f"{table_name} does not exist":
            print(f'{table_name}.pickleの書き込みをはじめます')
            dict_row = [
                dict(zip(record.keys(), record.values()))
                for record in table_fetch
            ]

    #print(dict_row)
    #print(table_fetch)

    # 書き込み
    # pickleファイルに書き込み
    await pickle_write(
        filename=table_name,
        table_fetch=dict_row
    )

    print(f'{table_name}.pickleの書き込みが終了しました')


async def line_pickle_table_create(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    LINEへの送信設定を示すテーブルの作成、更新

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    # テーブル名を代入
    table_name:str = f"{LINE_TABLE}{guild.id}"

    if db.conn == None:
        await db.connect()

    table_fetch = await db.select_rows(
        table_name=table_name,
        columns=[],
        where_clause={}
    )

    if len(table_fetch) > 0:
        # テーブルがない場合作成
        if 'does not exist' in table_fetch:
            await db.create_table(
                table_name=table_name,
                columns=LINE_COLUMNS
            )
            # 中身を空にする
            table_fetch = list()
        # テーブルがあって、中身もある場合
        else:
            # データベース側のカラムの型を入手
            table_columns_type = await db.get_columns_type(table_name=table_name)

            # テーブル内のカラムの型配列
            unchanged,table_fetch = await check_table_type(
                columns=LINE_COLUMNS,
                table_columns=table_columns_type,
                new_columns=LINE_NEW_COLUMNS,
                table_fetch=table_fetch
            )
            # テーブル内のカラム名配列
            guild_colums = [key for key in LINE_COLUMNS.keys()]
            table_colums = [key for key in table_columns_type.keys()]

            # テーブルの要素名か型が変更されていた場合、テーブルを削除し作成
            if table_colums != guild_colums or unchanged:
                await db.drop_table(table_name=table_name)
                await db.create_table(
                    table_name=table_name,
                    columns=LINE_COLUMNS
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
        guild_colums = [key for key in LINE_COLUMNS.keys()]
        table_colums = [key for key in table_columns_type.keys()]
        # テーブルの要素名が変更されていた場合、テーブルを削除し作成
        if table_colums != guild_colums:
            await db.drop_table(table_name=table_name)
            await db.create_table(
                table_name=table_name,
                columns=LINE_COLUMNS
            )

        row_list = list()

        for channel in guild.channels:
            row_value = LINE_NEW_COLUMNS
            row_value.update({
                "channel_id":channel.id,
                "guild_id":guild.id,
            })
            row_list.append(row_value)

        # まとめて作成(バッジ)
        await db.batch_insert_row(
            table_name=table_name,
            row_values=row_list
        )