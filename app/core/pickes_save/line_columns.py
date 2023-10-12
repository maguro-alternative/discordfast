from discord import Guild

from base.database import PostgresDB

from model_types.table_type import GuildLineChannel

from core.pickes_save.bin.get_channel import get_discord_channel, get_discord_thread
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

            channel_table = [
                GuildLineChannel(**row)
                for row in table_fetch
            ]

            # チャンネルの取得
            channels = await get_discord_channel(
                guild_id=guild.id,
                get_channel_type=LINE_TYPE
            )
            threads = await get_discord_thread(guild=guild)

            table_ids = [int(row.channel_id) for row in channel_table]

            # チャンネルのIDのリスト
            channel_ids = [channel.id for channel in channels]
            thread_ids = [thread.id for thread in threads]

            channel_ids.extend(thread_ids)

            if set(table_ids) != set(channel_ids):
                delete_channel_ids = list(set(table_ids) - set(channel_ids))
                insert_channel_ids = list(set(channel_ids) - set(table_ids))
                for del_channel_id in delete_channel_ids:
                    await db.delete_row(
                        table_name=table_name,
                        where_clause={
                            "channel_id":del_channel_id
                        }
                    )
                for channel_id in insert_channel_ids:
                    row_value = LINE_NEW_COLUMNS
                    row_value.update({
                        "channel_id":channel_id,
                        "guild_id":guild.id,
                    })
                    await db.insert_row(
                        table_name=table_name,
                        row_value=row_value
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

        threads = await get_discord_thread(guild=guild)
        row_list = list()

        for channel in guild.channels:
            row_value = LINE_NEW_COLUMNS
            row_value.update({
                "channel_id":channel.id,
                "guild_id":guild.id,
            })
            row_list.append(row_value)

        for thread in threads:
            row_value = LINE_NEW_COLUMNS
            row_value.update({
                "channel_id":thread.id,
                "guild_id":guild.id,
            })
            row_list.append(row_value)

        # まとめて作成(バッジ)
        await db.batch_insert_row(
            table_name=table_name,
            row_values=row_list
        )