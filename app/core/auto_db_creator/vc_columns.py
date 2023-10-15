from discord import Guild,ChannelType

from pkg.db.database import PostgresDB

from model_types.table_type import GuildVcChannel

from core.auto_db_creator.bin.get_channel import get_discord_channel
from core.auto_db_creator.bin.check_table import check_table_type
VC_TABLE = 'guilds_vc_signal'
VC_COLUMNS = {
    'vc_id'             : 'NUMERIC PRIMARY KEY',
    'guild_id'          : 'NUMERIC',
    'send_signal'       : 'boolean',
    'send_channel_id'   : 'NUMERIC',
    'join_bot'          : 'boolean',
    'everyone_mention'  : 'boolean',
    'mention_role_id'   : 'NUMERIC[]'
}
VC_NEW_COLUMNS = {
    'vc_id'             : 0,
    'guild_id'          : 0,
    'send_signal'       : True,
    'send_channel_id'   : 0,
    'join_bot'          : True,
    'everyone_mention'  : True,
    'mention_role_id'   : []
}
# 取得するチャンネルのタイプ
VC_TYPE = [2]

async def vc_pickle_table_create(
    db:PostgresDB,
    guild:Guild
) -> None:
    """
    ボイスチャンネルの入退室を管理するテーブルの作成、更新

    param:
    db:PostgresDB
        接続するデータベースのインスタンス
    guild:Guild
        Discordのサーバーインスタンス
    """
    # テーブル名を代入
    table_name:str = VC_TABLE

    if db.conn == None:
        await db.connect()

    table_fetch = await db.select_rows(
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
                columns=VC_COLUMNS
            )
            # 中身を空にする
            table_fetch = list()
        # テーブルがあって、中身もある場合
        else:
            # データベース側のカラムの型を入手
            table_columns_type = await db.get_columns_type(table_name=table_name)

            # テーブル内のカラムの型配列
            unchanged,table_fetch = await check_table_type(
                columns=VC_COLUMNS,
                table_columns=table_columns_type,
                new_columns=VC_NEW_COLUMNS,
                table_fetch=table_fetch
            )
            # テーブル内のカラム名配列
            guild_colums = [key for key in VC_COLUMNS.keys()]
            table_colums = [key for key in table_columns_type.keys()]

            # テーブルの要素名か型が変更されていた場合、テーブルを削除し作成
            if set(table_colums) != set(guild_colums) or unchanged:
                await db.drop_table(table_name=table_name)
                await db.create_table(
                    table_name=table_name,
                    columns=VC_COLUMNS
                )
                for row in table_fetch:
                    await db.insert_row(
                        table_name=table_name,
                        row_values=row
                    )

            vc_table = [
                GuildVcChannel(**row)
                for row in table_fetch
            ]

            guild_vc = await get_discord_channel(
                guild_id=guild.id,
                get_channel_type=VC_TYPE,
            )

            db_vc_ids = [int(row.vc_id) for row in vc_table]
            guild_vc_ids = [int(channel.id) for channel in guild_vc]

            if set(db_vc_ids) != set(guild_vc_ids):
                # データベースにあるが、サーバーにないチャンネルを削除
                delete_vc_ids = list(set(db_vc_ids) - set(guild_vc_ids))
                for vc_id in delete_vc_ids:
                    await db.delete_row(
                        table_name=table_name,
                        where_clause={
                            'vc_id':vc_id
                        }
                    )
                # サーバーにあるが、データベースにないチャンネルを追加
                add_vc_ids = list(set(guild_vc_ids) - set(db_vc_ids))
                system_channel_id = 0

                # システムチャンネルがある場合代入
                if hasattr(guild.system_channel,'id'):
                    system_channel_id = guild.system_channel.id

                for channel_id in add_vc_ids:
                    row_value = VC_NEW_COLUMNS
                    row_value.update({
                        "vc_id"             :channel_id,
                        "guild_id"          :guild.id,
                        'send_channel_id'   :system_channel_id
                    })
                    await db.insert_row(
                        table_name=table_name,
                        row_values=row_value
                    )

    # テーブルがあって、中身が空の場合
    if len(table_fetch) == 0:
        # データベース側のカラムの型を入手
        table_columns_type = await db.get_columns_type(table_name=table_name)

        # テーブル内のカラム名配列
        guild_colums = [key for key in VC_COLUMNS.keys()]
        table_colums = [key for key in table_columns_type.keys()]
        # テーブルの要素名が変更されていた場合、テーブルを削除し作成
        if set(table_colums) != set(guild_colums):
            await db.drop_table(table_name=table_name)
            await db.create_table(
                table_name=table_name,
                columns=VC_COLUMNS
            )

        system_channel_id = 0

        # システムチャンネルがある場合代入
        if hasattr(guild.system_channel,'id'):
            system_channel_id = guild.system_channel.id

        for channel in guild.channels:
            if channel.type == ChannelType.voice:
                row_value = VC_NEW_COLUMNS
                row_value.update({
                    "vc_id"             :channel.id,
                    "guild_id"          :guild.id,
                    'send_channel_id'   :system_channel_id
                })
                await db.insert_row(
                    table_name=table_name,
                    row_values=row_value
                )