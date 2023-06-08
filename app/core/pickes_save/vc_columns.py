from typing import List,Dict

from discord import Guild

from base.database import PostgresDB
from base.aio_req import (
    pickle_write
)

from core.pickes_save.bin.get_channel import get_discord_channel
from core.pickes_save.bin.check_table import check_table_type

VC_TABLE = 'guilds_vc_signal_'
VC_COLUMNS = {
    'vc_id': 'NUMERIC PRIMARY KEY', 
    'guild_id': 'NUMERIC', 
    'send_signal':'boolean',
    'send_channel_id': 'NUMERIC', 
    'join_bot': 'boolean',
    'everyone_mention': 'boolean',
    'mention_role_id':'NUMERIC[]'
}
VC_NEW_COLUMNS = {
    'vc_id': 0, 
    'guild_id': 0, 
    'send_signal':True,
    'send_channel_id': 0, 
    'join_bot': True,
    'everyone_mention': True,
    'mention_role_id':[]
}
# 取得するチャンネルのタイプ
VC_TYPE = [2]

async def vc_pickle_save(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    ボイスチャンネルの入退室を管理するテーブルの作成、更新
    キャッシュデータの作成

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    # テーブル名を代入
    table_name:str = f"{VC_TABLE}{guild.id}"

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
    channel_colums = [key for key in VC_COLUMNS.keys()]

    # テーブルがなかった場合、作成
    if len(table_fetch) > 0:
        # テーブルが存在しない場合、作成
        if (table_fetch[0] == f"{table_name} does not exist"):
            create_table_flag = True
            table_colums = [key for key in VC_COLUMNS.keys()]
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

    # テーブルの方が存在する場合
    if bool('table_columns_type' in locals()):
        # テーブル内のカラムの型配列
        unchanged,table_fetch = await check_table_type(
            columns=VC_COLUMNS,
            table_columns=table_columns_type,
            new_columns=VC_NEW_COLUMNS,
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
            table_colums = [key for key in VC_COLUMNS.keys()]

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
            columns=VC_COLUMNS
        )

    # テーブルに変更があった場合
    if changed_table_flag and len(table_fetch) != 0:
        if "does not exist" not in table_fetch[0]:
            # まとめて作成(バッジ)
            await db.batch_insert_row(
                table_name=table_name,
                row_values=table_fetch
            )

    # 中身が空の場合
    if len(table_fetch) == 0 or create_table_flag:

        # Discordのチャンネルを取得
        all_channel = await get_discord_channel(
            guild_id=guild.id,
            get_channel_type=VC_TYPE
        )

        row_values = []

        for channel in all_channel:
            row = {}
            for key,values in VC_NEW_COLUMNS.items():
                # 各要素を更新
                if key == "vc_id":
                    value = channel["id"]
                elif key == "guild_id":
                    value = guild.id
                elif key == "send_channel_id":
                    # システムチャンネルがある場合代入
                    if hasattr(guild.system_channel,'id'):
                        value = guild.system_channel.id
                    else:
                        value = 0
                else:
                    value = values
                row.update({key:value})
            
            row_values.append(row)

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

    # テーブルに中身がある場合
    if len(table_fetch) > 0:
        if table_fetch[0] != f"{table_name} does not exist":
            print(f'{table_name}.pickleの書き込みをはじめます')
            dict_row = [
                dict(zip(record.keys(), record.values())) 
                for record in table_fetch
            ]


    # 書き込み
    # pickleファイルに書き込み
    await pickle_write(
        filename=table_name,
        table_fetch=dict_row
    )

    print(f'{table_name}.pickleの書き込みが終了しました')
