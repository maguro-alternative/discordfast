from discord import Guild

from base.database import PostgresDB
from base.aio_req import (
    pickle_write
)

from typing import List,Dict

from core.pickes_save.bin.check_table import check_table_type

WEBHOOK_TABLE = 'webhook_'
WEBHOOK_COLUMNS = {
    'uuid':'UUID PRIMARY KEY',
    'guild_id': 'NUMERIC', 
    'webhook_id':'NUMERIC',
    'subscription_type':'VARCHAR(50)',
    'subscription_id': 'VARCHAR(50)',
    'mention_roles':'NUMERIC[]',
    'mention_members':'NUMERIC[]',
    'ng_or_word':'VARCHAR(50)[]',
    'ng_and_word':'VARCHAR(50)[]',
    'search_or_word':'VARCHAR(50)[]',
    'search_and_word':'VARCHAR(50)[]',
    'mention_or_word':'VARCHAR(50)[]',
    'mention_and_word':'VARCHAR(50)[]',
    'created_at':'VARCHAR(50)'
}
WEBHOOK_NEW_COLUMNS = {
    'uuid':'',
    'guild_id': 0, 
    'webhook_id':0,
    'subscription_type':'',
    'subscription_id': '',
    'mention_roles':[],
    'mention_members':[],
    'ng_or_word':[],
    'ng_and_word':[],
    'search_or_word':[],
    'search_and_word':[],
    'mention_or_word':[],
    'mention_and_word':[],
    'created_at':''
}

async def webhook_pickle_save(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    webhook設定のテーブルの作成、更新
    キャッシュデータの作成

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    # Webhookのテーブル
    table_name = f"{WEBHOOK_TABLE}{guild.id}"
    table_fetch:List[Dict] = await db.select_rows(
        table_name=table_name,
        columns=[],
        where_clause={}
    )

    # データベース側のカラムの型を入手
    table_columns_type = await db.get_columns_type(table_name=table_name)

    # テーブル内のカラム名配列
    webhook_colums = [key for key in WEBHOOK_COLUMNS.keys()]
    table_colums = [key for key in table_columns_type.keys()]

    # テーブル内のカラムの型配列
    unchanged,table_fetch = await check_table_type(
        columns=WEBHOOK_COLUMNS,
        table_columns=table_columns_type,
        new_columns=WEBHOOK_NEW_COLUMNS,
        table_fetch=table_fetch
    )

    # テーブルに変更があるかのフラグ
    changed_table_flag = table_colums != webhook_colums or unchanged != False


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
    # テーブルが存在しているが、中身が空の場合
    elif len(table_fetch) == 0:
        print(f'テーブル:{table_name}の要素は空です')
        # 中身が空かつ、要素が変更されていた場合
        if changed_table_flag:
            drop_table_flag = True
        else:
            table_colums = [key for key in WEBHOOK_COLUMNS.keys()]
        
    # データベース側のカラムを格納
    if create_colum_flag:
        print(f'テーブル:{table_name}のカラム名一覧を作成します')
        table_colums = [key for key in table_fetch[0].keys()]
        
    # カラムの構成が変更されていた場合、削除し新たに作成する
    if changed_table_flag or drop_table_flag:
        print(f'テーブル:{table_name}を削除します')
        create_table_flag = True
        await db.drop_table(table_name=f"{table_name}")

    # テーブルの作成
    if create_table_flag:
        print(f'テーブル:{table_name}を作成します')
        await db.create_table(
            table_name=table_name,
            columns=WEBHOOK_COLUMNS
        )

    # テーブルに変更があった場合
    if changed_table_flag and len(table_fetch) != 0:
        # まとめて作成(バッジ)
        for table_row in table_fetch:
            #print(table_row)
            await db.insert_row(
                table_name=table_name,
                row_values=table_row
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