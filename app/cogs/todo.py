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
        #self.todo_signal.start()

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
            return
        if timelimit < datetime.now():
            respond_text = "期日が不正です。"
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

        task_fetch:List[Dict] = [
            task
            for task in table_fatch
            if int(task.get('task_number')) == task_number
        ]

        await db.disconnect()

        respond_text = f"タスク終了:{task_fetch[0].get('title')}\n"

        if task_fetch[0].get('alert_role') != 0:
            respond_text += f"<@&{task_fetch[0].get('alert_role')}> "
        if task_fetch[0].get('alert_user') != 0:
            respond_text += f"<@{task_fetch[0].get('alert_user')}>"

        respond_text += f"\n備考:{description}"

        await ctx.respond(respond_text)

        await pickle_write(
            filename=table_name,
            table_fetch=table_fatch
        )

    @tasks.loop(seconds=60)
    async def todo_signal(self):
        # Botが起動しないとサーバを取得できない
        # なので起動時の読み込みでは機能しない
        now_time = datetime.now()
        for guild in self.bot.guilds:
            table_name = f"task_{guild.id}"

            discord_bor_api = ReqestDiscord(
                guild_id=guild.id,
                limit=100,
                token=DISCORD_BOT_TOKEN
            )

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

            for task in table_fetch:
                time_limit_str:str = task.get('time_limit')
                time_limit = datetime.strptime(
                    time_limit_str,
                    '%Y-%m-%d %H:%M'
                )
                limit = time_limit - now_time
                
                limit_five_day:bool = limit.seconds > 431939 and limit.seconds < 432001
                limit_four_day:bool = limit.seconds > 345539 and limit.seconds < 345601
                limit_tree_day:bool = limit.seconds > 259139 and limit.seconds < 259201
                limit_two_day:bool = limit.seconds > 172739 and limit.seconds < 172801
                limit_one_day:bool = limit.seconds > 86339 and limit.seconds < 86461
                limit_half_day:bool = limit.seconds > 43169 and limit.seconds < 43231
                limit_six_hour:bool = limit.seconds > 21554 and limit.seconds < 21616
                limit_tree_hour:bool = limit.seconds > 10747 and limit.seconds < 10808
                limit_two_hour:bool = limit.seconds > 7139 and limit.seconds < 7201
                limit_one_hour:bool = limit.seconds > 3539 and limit.seconds < 3601
                limit_50_min:bool = limit.seconds > 2939 and limit.seconds < 3001
                limit_40_min:bool = limit.seconds > 2339 and limit.seconds < 2401
                limit_30_min:bool = limit.seconds > 1739 and limit.seconds < 1801
                limit_20_min:bool = limit.seconds > 1139 and limit.seconds < 1201
                limit_10_min:bool = limit.seconds > 539 and limit.seconds < 601

                text = f"{task.get('task_title')}が未達成です。\n期日:{task.get('time_limit')}\n達成している場合は/todo_completionで完了報告してください。"

                if task.get('alert_role') != 0:
                    text = f"<@&{int(task.get('alert_role'))}> " + text
                if task.get('alert_user') != 0:
                    text = f"<@&{int(task.get('alert_user'))}> " + text

                if limit.days >= 0:
                    if task.get('alert_level') == 1:
                        # 残り1日の場合
                        if (limit_one_day or limit_half_day or 
                            limit_six_hour or limit_one_hour or
                            limit_30_min or limit_10_min
                            ):
                            await discord_bor_api.send_discord(
                                channel_id=int(task.get('task_channel')),
                                message=text
                            )
                    
                    if task.get('alert_level') == 2:
                        # 残り2日の場合
                        if (limit_two_day or limit_one_day or limit_half_day or 
                            limit_six_hour or limit_tree_hour or limit_one_hour or
                            limit_50_min or limit_30_min or limit_10_min
                            ):
                            await discord_bor_api.send_discord(
                                channel_id=int(task.get('task_channel')),
                                message=text
                            )

                    if task.get('alert_level') == 3:
                        # 残り3日の場合
                        if (limit_tree_day or limit_two_day or 
                            limit_one_day or limit_half_day or 
                            limit_six_hour or limit_tree_hour or 
                            limit_two_hour or limit_one_hour or
                            limit_50_min or limit_40_min or 
                            limit_30_min or limit_10_min
                            ):
                            await discord_bor_api.send_discord(
                                channel_id=int(task.get('task_channel')),
                                message=text
                            )

                    if task.get('alert_level') == 4:
                        # 残り4日の場合
                        if (limit_four_day or limit_tree_day or limit_two_day or 
                            limit_one_day or limit_half_day or 
                            limit_six_hour or limit_tree_hour or 
                            limit_two_hour or limit_one_hour or
                            limit_50_min or limit_40_min or 
                            limit_30_min or limit_10_min
                            ):
                            await discord_bor_api.send_discord(
                                channel_id=int(task.get('task_channel')),
                                message=text
                            )

                    if task.get('alert_level') == 5:
                        # 残り5日の場合
                        if (limit_five_day or limit_four_day or 
                            limit_tree_day or limit_two_day or 
                            limit_one_day or limit_half_day or 
                            limit_six_hour or limit_tree_hour or 
                            limit_two_hour or limit_one_hour or
                            limit_50_min or limit_40_min or 
                            limit_30_min or limit_20_min or limit_10_min
                            ):
                            await discord_bor_api.send_discord(
                                channel_id=int(task.get('task_channel')),
                                message=text
                            )

                    # 10分前ならレベル関係なくアラートを出す
                    if limit.seconds < 600:
                        await discord_bor_api.send_discord(
                            channel_id=int(task.get('task_channel')),
                            message=text
                        )





def setup(bot:DBot):
    return bot.add_cog(Todo(bot))