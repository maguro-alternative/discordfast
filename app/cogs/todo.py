from discord.ext import commands
from discord import Option
import discord

try:
    # Botのみ起動の場合
    from app.core.start import DBot
    from app.core.db_create import DB
    from app.model_types.environ_conf import EnvConf
except ModuleNotFoundError:
    from core.start import DBot
    from core.db_create import DB
    from model_types.environ_conf import EnvConf

from datetime import datetime
from typing import Dict,List

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

TASK_COLUMN = {
    'task_number'   :'BIGSERIAL PRIMARY KEY',
    'guild_id'      :'NUMERIC',
    'task_title'    :'VARCHAR(50)',
    'time_limit'    :'VARCHAR(50)',
    'task_channel'  :'NUMERIC',
    'alert_level'   :'SMALLINT',
    'alert_role'    :'NUMERIC',
    'alert_user'    :'NUMERIC'
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
            #await asyncio.sleep(5)
            if DB.conn == None:
                await DB.connect()

            table_name = f"task_table"

            table_fetch = await DB.select_rows(
                table_name=table_name,
                columns=[],
                where_clause={
                    'guild_id':ctx.guild_id
                }
            )

            # テーブルがない場合、作成
            if len(table_fetch) == 1:
                if "does not exist" in table_fetch[0]:
                    await DB.create_table(
                        table_name=table_name,
                        columns=TASK_COLUMN
                    )

            row_value = {
                'task_title':title,
                'guild_id':ctx.guild_id,
                'time_limit':timelimit.strftime('%Y-%m-%d %H:%M'),
                'task_channel':ctx.channel_id,
                'alert_level':alert_level,
                'alert_role':alert_role_id,
                'alert_user':alert_user_id
            }

            await DB.insert_row(
                table_name=table_name,
                row_values=row_value
            )

            table_fetch = await DB.select_rows(
                table_name=table_name,
                columns=[],
                where_clause={
                    'guild_id':ctx.guild_id
                }
            )

            task_number = table_fetch[-1]['task_number']
            # 変更URL
            url = (EnvConf.LINE_CALLBACK_URL.replace('/line-callback/','')) + f'/guild/{ctx.guild_id}'

            await ctx.respond(f"番号は**{task_number}**です。\n一覧はこちら:{url}")

        except:
            await ctx.respond("登録がうまくいきませんでした。もう一度やり直してください。")

    @commands.slash_command(description="タスク完了")
    async def todo_completion(
        self,
        ctx:discord.ApplicationContext,
        task_number: Option(int, required=True, description="タスク番号",),
        description: Option(str, required=False, description="備考"),
    ):
        table_name = f"task_table"

        await ctx.respond("処理中...")

        # データベースに接続
        if DB.conn == None:
            await DB.connect()

        table_fetch:List[Dict] = await DB.select_rows(
            table_name=table_name,
            columns=[],
            where_clause={
                'task_number':task_number
            }
        )

        if len(table_fetch) == 1:
            if "does not exist" in table_fetch[0]:
                await ctx.respond("該当するタスクが見当たりません。")
                return
        if len(table_fetch) == 0:
            await ctx.respond("該当するタスクが見当たりません。")
            return

        # タスク削除
        await DB.delete_row(
            table_name=table_name,
            where_clause={
                'task_number':task_number
            }
        )

        if len(table_fetch) == 0:
            await ctx.respond("該当するタスクが見当たりません。")
            return

        respond_text = f"タスク終了:{table_fetch[0].get('task_title')}\n"

        if table_fetch[0].get('alert_role') != 0:
            respond_text += f"<@&{int(table_fetch[0].get('alert_role'))}> "
        if table_fetch[0].get('alert_user') != 0:
            respond_text += f"<@{int(table_fetch[0].get('alert_user'))}>"

        respond_text += f"\n備考:{description}"

        await ctx.respond(respond_text)


def setup(bot:DBot):
    return bot.add_cog(Todo(bot))