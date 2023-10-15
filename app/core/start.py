import discord
from discord import Intents
import os
import json
import traceback
import requests,json

from model_types.environ_conf import EnvConf

from core.db_create import db_auto_creator

class DBot(discord.AutoShardedBot):
    def __init__(self, token:str, intents:Intents) -> None:
        self.token = token
        super().__init__(intents = intents)
        self.load_cogs()

    def load_cogs(self) -> None:
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                cog = file[:-3]
                self.load_extension(f"cogs.{cog}")
                print(cog + "をロードしました")

    async def db_get(self) -> None:
        # データベースへ接続
        await db_auto_creator(guilds=self.guilds)

    # 起動用の補助関数です
    def run(self) -> None:
        try:
            self.loop.run_until_complete(self.start(self.token))
        except discord.LoginFailure:
            print("Discord Tokenが不正です")
        except KeyboardInterrupt:
            print("終了します")
        except discord.HTTPException as e:
            traceback.print_exc()
            if e.status == 429 and EnvConf.WEBHOOK != None:
                main_content = {'content': 'DiscordBot 429エラー\n直ちにDockerファイルを再起動してください。'}
                headers      = {'Content-Type': 'application/json'}

                requests.post(
                    url=EnvConf.WEBHOOK,
                    data=json.dumps(main_content),
                    headers=headers
                )

        except Exception as e:
            traceback.print_exc()
            if EnvConf.WEBHOOK != None:
                if EnvConf.ADMIN_ID != None:
                    admin_id = EnvConf.ADMIN_ID
                    text = f"<@{int(admin_id)}> {e}"
                else:
                    text = str(e)
                main_content = {
                    'content':text
                }
                headers = {
                    'Content-Type': 'application/json'
                }
                requests.post(
                    url=EnvConf.WEBHOOK,
                    data=json.dumps(main_content),
                    headers=headers
                )