import asyncpg
from asyncpg.connection import Connection 
from asyncpg.exceptions import DuplicateTableError
import asyncio
import os

from typing import List

from dotenv import load_dotenv
load_dotenv()


class DataBaseNotConnect(Warning):...

class PostgresDB:
    def __init__(
            self,
            user:str, 
            password:str, 
            database:str, 
            host:str
    ):
        """
        PostgreSQLのクラス

        user    :str
            Postgresのユーザー名
        password:str
            パスワード
        database:str
            データベースの名前
        host    :str
            ホスト番号
        conn    :Connection
            データベースの接続情報
        """
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.conn:Connection = None

    async def connect(self):
        """
        PostgreSQLへ接続
        """
        self.conn = await asyncpg.connect(
            user=self.user, 
            password=self.password, 
            database=self.database, 
            host=self.host
        )

    async def disconnect(self):
        """
        PostgreSQLの切断
        """
        if self.conn == None:
            raise DataBaseNotConnect
        await self.conn.close()

    async def create_table(self, table_name:str, columns:dict) -> str:
        """
        テーブルの作成

        table_name  :str
            作成するテーブル名
        colums      :dict
            テーブル内の名前と型
        """
        if self.conn == None:
            raise DataBaseNotConnect
        columns_str = ', '.join(
            [
                f"{column_name} {data_type}" for column_name, data_type in columns.items()
            ]
        )
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str});"
        try:
            await self.conn.execute(sql)
            return "ok"
        except DuplicateTableError:
            return "DuplicateTableError"
        
    async def drop_table(self, table_name:str):
        """
        テーブルの削除

        table_name:str
            削除するテーブルの名前
        """
        sql = f"DROP TABLE IF EXISTS {table_name};"
        await self.conn.execute(sql)

    async def select_rows(
        self, 
        table_name:str, 
        columns:List[str]=None, 
        where_clause:dict=None
    ) -> list:
        """
        テーブルの参照
        
        table_name  :str
            参照するテーブルの名前
        columns     :List[str]
            参照する列、指定がない場合すべてを参照
        where_clause:dict
            条件

        return:

        list        :List[Any]
        """
        if self.conn == None:
            raise DataBaseNotConnect
        if columns is None or len(columns) == 0:
            columns_str = '*'
        else:
            columns_str = ', '.join(columns)

        if where_clause is None:
            sql = f"SELECT {columns_str} FROM {table_name};"
        else:
            where_clause_str = ' AND '.join(
                [
                    f"{column}=${i+1}" for i, column in enumerate(
                        where_clause.keys()
                    )
                ]
            )
            where_clause_values = list(where_clause.values())
            sql = f"SELECT {columns_str} FROM {table_name} "
            if where_clause_str:
                sql += f"WHERE {where_clause_str};"
            else:
                sql += ";"

        try:
            return await self.conn.fetch(sql, *where_clause_values)
        except asyncpg.exceptions.UndefinedTableError:
            return [f"{table_name} does not exist"]

    async def insert_row(
        self, 
        table_name:str, 
        row_values:dict
    ) -> bool:
        """
        行の追加
        
        table_name:str
            対象のテーブルの名前
        row_values:dict
            追加する行の内容
        """
        if self.conn == None:
            raise DataBaseNotConnect
        columns_str = ', '.join(row_values.keys())
        values_str = ', '.join(
            [
                f"${i+1}" for i in range(len(row_values))
            ]
        )
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
        try:
            await self.conn.execute(sql, *row_values.values())
            return True
        except asyncpg.exceptions.UniqueViolationError:
            return False

    async def update_row(
        self, 
        table_name:str, 
        row_values:dict, 
        where_clause:dict
    ):
        """
        行の更新
        
        table_name  :str 
            テーブルの名前
        row_values  :dict 
            更新の内容
        where_clause:dict
            条件
        """
        if self.conn == None:
            raise DataBaseNotConnect
        
        """
        set_clause = []
        for column, value in row_values.items():
            if isinstance(value, (list, tuple)) and array_append:
                set_clause.append(f"{column} = array_cat({column}, $1)")
            else:
                if column in set_clause:
                    set_index = set_clause.index(column)
                else:
                    set_index = 0
                set_clause.append(f"{column} = ${len(where_clause) + set_index + 1}")
        set_clause_str = ', '.join(set_clause)
        """

        
        set_clause_str = ', '.join(
            [
                f"{column}=${i+1}" for i, column in enumerate(
                    row_values.keys()
                )
            ]
        )
        
        where_clause_str = ' AND '.join(
            [
                f"{column}=${i+len(row_values)+1}" for i, column in enumerate(
                    where_clause.keys()
                )
            ]
        )
        values = list(row_values.values()) + list(where_clause.values())
        sql = f"UPDATE {table_name} SET {set_clause_str} "
        if where_clause_str:
            sql += f"WHERE {where_clause_str};"
        else:
            sql += ";"
        await self.conn.execute(sql, *values)

    async def delete_row(
        self, 
        table_name:str, 
        where_clause:dict
    ):
        """
        行の削除
        
        table_name  :str 
            テーブルの名前
        where_clause:dict
            条件
        """
        if self.conn == None:
            raise DataBaseNotConnect
        where_clause_str = ' AND '.join(
            [
                f"{column}=${i+1}" for i, column in enumerate(
                    where_clause.keys()
                )
            ]
        )
        where_clause_values = list(where_clause.values())
        sql = f"DELETE FROM {table_name} "
        if where_clause_str:
            sql += f"WHERE {where_clause_str};"
        else:
            sql += ";"
        await self.conn.execute(sql, *where_clause_values)

async def main():
    user = os.getenv('PGUSER')
    password = os.getenv('PGPASSWORD')
    database = os.getenv('PGDATABASE')
    host = os.getenv('PGHOST')
    db = PostgresDB(
        user=user,
        password=password,
        database=database,
        host=host
    )
    columns = {
        'guild_id': 'DECIMAL PRIMARY KEY', 
        'channel_id': 'DECIMAL[]', 
        'channel_type': 'VARCHAR(50)',
        'message_type': 'VARCHAR(50)',
        'message_bot': 'BOOLEAN',
        'channel_nsfw': 'BOOLEAN'
    }
    await db.connect()

    await db.drop_table(table_name='users')
    await db.create_table(table_name='guilds_ng_channel',columns=columns)
    # データベースのクエリを実行する処理をここに書く
    row_values = {
        'guild_id': 838937935822585928, 
        'channel_id': [911602953373241344,872822898946105396], 
        'channel_type': 'voice',
        'message_type': 'pins_add',
        'message_bot': True,
        'channel_nsfw': False
    }

    #await db.insert_row(table_name='guilds_ng_channel',row_values=row_values)

    row_values = {
        #'channel_id': f'array_append(channel_id, {928284688181772309})'
        'channel_id': [928284688181772309]
    }

    where_clause = {
        'guild_id': 838937935822585928
    }

    await db.update_row(
        table_name='guilds_ng_channel',
        row_values=row_values,
        where_clause=where_clause
    )
    await db.disconnect()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
