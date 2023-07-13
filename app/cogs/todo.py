from discord.ext import commands,tasks
from discord import Option
import discord

import aiohttp

try:
    # Botのみ起動の場合
    from app.core.start import DBot
except ModuleNotFoundError:
    from core.start import DBot

from dotenv import load_dotenv
load_dotenv()

import os

from datetime import datetime,timezone
from typing import Dict,List

from base.database import PostgresDB
from base.aio_req import (
    pickle_read,
    pickle_write
)

from message_type.discord_type.message_creater import ReqestDiscord

USER = os.getenv('PGUSER')
PASSWORD = os.getenv('PGPASSWORD')
DATABASE = os.getenv('PGDATABASE')
HOST = os.getenv('PGHOST')
db = PostgresDB(
    user=USER,
    password=PASSWORD,
    database=DATABASE,
    host=HOST
)

DISCORD_BASE_URL = "https://discord.com/api"

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

TASK_COLUMN = {
    'task_number':'BIGSERIAL PRIMARY KEY',
    'task_title':'VARCHAR(50)',
    'time_limit':'VARCHAR(50)',
    'task_channel':'NUMERIC',
    'alert_level':'SMALLINT',
    'alert_role':'NUMERIC',
    'alert_user':'NUMERIC'
}


class Todo(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot

    @commands.slash_command(description="タスクの登録")
    async def todo_register(
        self,
        ctx:discord.ApplicationContext,
        title: Option(str, required=True, description="タスク名",),
        timelimit_year:Option(int, required=True, description="期日(年)",),
        timelimit_month:Option(int, required=True, description="期日(月)",),
        timelimit_day:Option(int, required=True, description="期日(日)",),
        timelimit_hour:Option(int, required=True, description="期日(時間)",),
        timelimit_minute:Option(int, required=True, description="期日(分)",),
        alert_level:Option(int, required=True, description="アラートレベル(1~5)",),
        alert_role:Option(discord.Role, required=False, description="通知するロール"),
        alert_user:Option(discord.User, required=False, description="通知するユーザ"),
    ):
        alert_user_id = 0
        alert_role_id = 0

        if type(alert_role) is discord.Role:
            alert_role_id = alert_role.id

        if type(alert_user) is discord.User:
            alert_user_id = alert_user.id

        respond_text = ""
        timelimit = datetime.strptime(
            f'{timelimit_year}-{timelimit_month}-{timelimit_day} {timelimit_hour}:{timelimit_minute}',
            '%Y-%m-%d %H:%M'
        )
        if alert_level < 1 or alert_level > 5:
            respond_text = "アラートレベルが不正です。"
            await ctx.respond(respond_text)
            return
        if timelimit < datetime.now():
            respond_text = "期日が不正です。"
            await ctx.respond(respond_text)
            return
        else:
            respond_text = f"タスク名:{title}\n"
            respond_text += f"期日:{timelimit_year}年{timelimit_month}月{timelimit_day}日{timelimit_hour}時{timelimit_minute}分\n"
            respond_text += f"アラートレベル:{alert_level}\n"
            respond_text += f"タスク対象:"
            if alert_role != None:
                respond_text += f"<@&{alert_role.id}> "
            if alert_user != None:
                respond_text += f" <@{alert_user.id}>"

        await ctx.respond(respond_text)

        try:
            await db.connect()

            table_name = f"task_{ctx.guild_id}"

            table_fetch = await db.select_rows(
                table_name=table_name,
                columns=[],
                where_clause={}
            )

            # テーブルがない場合、作成
            if len(table_fetch) == 1:
                if "does not exist" in table_fetch[0]:
                    await db.create_table(
                        table_name=table_name,
                        columns=TASK_COLUMN
                    )

            row_value = {
                'task_title':title,
                'time_limit':timelimit.strftime('%Y-%m-%d %H:%M'),
                'task_channel':ctx.channel_id,
                'alert_level':alert_level,
                'alert_role':alert_role_id,
                'alert_user':alert_user_id
            }

            await db.insert_row(
                table_name=table_name,
                row_values=row_value
            )

            table_fetch = await db.select_rows(
                table_name=table_name,
                columns=[],
                where_clause={}
            )

            await pickle_write(
                filename=table_name,
                table_fetch=table_fetch
            )

            await db.disconnect()
        except:
            await ctx.respond("登録がうまくいきませんでした。もう一度やり直してください。")

        task_number = table_fetch[-1]['task_number']
        # 変更URL
        url = (os.environ.get('LINE_CALLBACK_URL').replace('/line-callback/','')) + f'/guild/{ctx.guild_id}'

        await ctx.respond(f"番号は**{task_number}**です。\n一覧はこちら:{url}")

    @commands.slash_command(description="タスク完了")
    async def todo_completion(
        self,
        ctx:discord.ApplicationContext,
        task_number: Option(int, required=True, description="タスク番号",),
        description: Option(str, required=False, description="備考"),
    ):
        table_name = f"task_{ctx.guild_id}"

        await ctx.respond("処理中...")

        try:
            table_fetch:List[Dict] = await pickle_read(
                filename=table_name
            )
        except FileNotFoundError:
            # pickleファイルがない場合、データベースに接続
            await db.connect()

            table_fetch:List[Dict] = await db.select_rows(
                table_name=table_name,
                columns=[],
                where_clause={}
            )

            await db.disconnect()

            if len(table_fetch) == 1:
                if "does not exist" in table_fetch[0]:
                    table_fetch = list()
                else:
                    await pickle_write(
                        filename=table_name,
                        table_fetch=table_fetch
                    )
            else:
                await pickle_write(
                    filename=table_name,
                    table_fetch=table_fetch
                )

        await db.connect()

        task_fetch:List[Dict] = await db.select_rows(
            table_name=table_name,
            columns=[],
            where_clause={
                'task_number':task_number
            }
        )

        # タスク削除
        await db.delete_row(
            table_name=table_name,
            where_clause={
                'task_number':task_number
            }
        )

        table_fatch:List[Dict] = await db.select_rows(
            table_name=table_name,
            columns=[],
            where_clause={}
        )

        await db.disconnect()

        if len(task_fetch) == 0:
            await ctx.respond("該当するタスクが見当たりません。")
            return

        respond_text = f"タスク終了:{task_fetch[0].get('task_title')}\n"

        if task_fetch[0].get('alert_role') != 0:
            respond_text += f"<@&{int(task_fetch[0].get('alert_role'))}> "
        if task_fetch[0].get('alert_user') != 0:
            respond_text += f"<@{int(task_fetch[0].get('alert_user'))}>"

        respond_text += f"\n備考:{description}"

        await ctx.respond(respond_text)

        await pickle_write(
            filename=table_name,
            table_fetch=table_fatch
        )





def setup(bot:DBot):
    return bot.add_cog(Todo(bot))