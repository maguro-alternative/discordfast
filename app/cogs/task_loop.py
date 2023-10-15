from discord.ext import commands,tasks
import aiohttp

try:
    # Botのみ起動の場合
    from app.core.start import DBot
    from app.core.db_create import DB
    from app.cogs.bin.webhook_sub.twitter_sub import twitter_subsc
    from app.cogs.bin.webhook_sub.niconico_sub import niconico_subsc
    from app.cogs.bin.webhook_sub.youtube_sub import youtube_subsc
    from app.model_types.discord_type.message_creater import ReqestDiscord
    from app.model_types.table_type import WebhookSet
    from app.model_types.environ_conf import EnvConf
except ModuleNotFoundError:
    from core.start import DBot
    from core.db_create import DB
    from cogs.bin.webhook_sub.twitter_sub import twitter_subsc
    from cogs.bin.webhook_sub.niconico_sub import niconico_subsc
    from cogs.bin.webhook_sub.youtube_sub import youtube_subsc
    from model_types.discord_type.message_creater import ReqestDiscord
    from model_types.table_type import WebhookSet
    from model_types.environ_conf import EnvConf

from typing import Dict,List
from datetime import datetime
import traceback

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

TASK_COLUMN = {
    'task_number':'BIGSERIAL PRIMARY KEY',
    'task_title':'VARCHAR(50)',
    'time_limit':'VARCHAR(50)',
    'task_channel':'NUMERIC',
    'alert_level':'SMALLINT',
    'alert_role':'NUMERIC',
    'alert_user':'NUMERIC'
}

class Task_Loop(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot
        self.task_loop.start()

    @tasks.loop(seconds=60)
    async def task_loop(self):
        # Botが起動しないとサーバを取得できない
        # なので起動時の読み込みでは機能しない
        now_time = datetime.now()
        try:
            for guild in self.bot.guilds:
                webhook_table_name = f"webhook_set"
                task_table_name = f"task_table"

                if DB.conn == None:
                    await DB.connect()

                discord_bor_api = ReqestDiscord(
                    guild_id=guild.id,
                    limit=100,
                    token=DISCORD_BOT_TOKEN
                )
                # 読み取り
                webhook_table:List[Dict] = await DB.select_rows(
                    table_name=webhook_table_name,
                    columns=[],
                    where_clause={
                        'guild_id':guild.id
                    }
                )
                webhook_fetch = [
                    WebhookSet(**w)
                    for w in webhook_table
                ]
                guild_webhooks = await guild.webhooks()

                # 登録してあるwebhookを一つ一つ処理
                for webhook in webhook_fetch:
                    for guild_webhook in guild_webhooks:
                        if guild_webhook.id == int(webhook.webhook_id):
                            webhook_url = guild_webhook.url
                            break

                    if not bool('webhook_url' in locals()):
                        break

                    # twitterの場合
                    if webhook.subscription_type == 'twitter':
                        await twitter_subsc(
                            webhook=webhook,
                            webhook_url=webhook_url,
                            table_name=webhook_table_name
                        )

                    # niconicoの場合
                    if webhook.subscription_type == 'niconico':
                        await niconico_subsc(
                            webhook=webhook,
                            webhook_url=webhook_url,
                            table_name=webhook_table_name
                        )

                    # youtubeの場合
                    if webhook.subscription_type == 'youtube':
                        await youtube_subsc(
                            webhook=webhook,
                            webhook_url=webhook_url,
                            table_name=webhook_table_name
                        )

                table_fetch:List[Dict] = await DB.select_rows(
                    table_name=task_table_name,
                    columns=[],
                    where_clause={
                        'guild_id':guild.id
                    }
                )

                if len(table_fetch) == 1:
                    if "does not exist" in table_fetch[0]:
                        table_fetch = list()

                for task in table_fetch:
                    time_limit_str:str = task.get('time_limit')
                    time_limit = datetime.strptime(
                        time_limit_str,
                        '%Y-%m-%d %H:%M'
                    )
                    limit = time_limit - now_time

                    # 日付は秒数に含まれないため含める
                    limit_day_seconds = limit.seconds + limit.days * 86400

                    limit_five_day:bool = limit_day_seconds > 431939 and limit_day_seconds < 432001
                    limit_four_day:bool = limit_day_seconds > 345539 and limit_day_seconds < 345601
                    limit_tree_day:bool = limit_day_seconds > 259139 and limit_day_seconds < 259201
                    limit_two_day:bool = limit_day_seconds > 172739 and limit_day_seconds < 172801
                    limit_one_day:bool = limit_day_seconds > 86339 and limit_day_seconds < 86461
                    limit_half_day:bool = limit_day_seconds > 43169 and limit_day_seconds < 43231
                    limit_six_hour:bool = limit_day_seconds > 21554 and limit_day_seconds < 21616
                    limit_tree_hour:bool = limit_day_seconds > 10747 and limit_day_seconds < 10808
                    limit_two_hour:bool = limit_day_seconds > 7139 and limit_day_seconds < 7201
                    limit_one_hour:bool = limit_day_seconds > 3539 and limit_day_seconds < 3601
                    limit_50_min:bool = limit_day_seconds > 2939 and limit_day_seconds < 3001
                    limit_40_min:bool = limit_day_seconds > 2339 and limit_day_seconds < 2401
                    limit_30_min:bool = limit_day_seconds > 1739 and limit_day_seconds < 1801
                    limit_20_min:bool = limit_day_seconds > 1139 and limit_day_seconds < 1201
                    limit_10_min:bool = limit_day_seconds > 539 and limit_day_seconds < 601

                    text = f"{task.get('task_title')}が未達成です。\nタスクナンバー:{task.get('task_number')}\n期日:{task.get('time_limit')}\n達成している場合は/todo_completionで完了報告してください。"

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
                                print(f"level 1:{limit_day_seconds}")

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
                                print(f"level 2:{limit_day_seconds}")

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
                                print(f"level 3:{limit_day_seconds}")

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
                                print(f"level 4:{limit_day_seconds}")

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
                                print(f"level 5:{limit_day_seconds}")

                        # 10分前ならレベル関係なくアラートを出す
                        if limit_day_seconds < 600:
                            await discord_bor_api.send_discord(
                                channel_id=int(task.get('task_channel')),
                                message=text
                            )
                            print(f"{task.get('task_title')}終了まで残り{limit.seconds}秒")
        except Exception as e:
            if bool('webhook_url' in locals()):
                if webhook_url == None:
                    webhook_url = EnvConf.WEBHOOK
            else:
                webhook_url = EnvConf.WEBHOOK
            async with aiohttp.ClientSession() as sessions:
                async with sessions.post(
                    url=webhook_url,
                    data={
                        'content':f"エラーが発生しました。\n```{e}\n{traceback.format_exc()}```"
                    }
                ) as re:
                    print(e)

def setup(bot:DBot):
    return bot.add_cog(Task_Loop(bot))