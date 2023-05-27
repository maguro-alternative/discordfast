import discord
from discord import Intents
import os
import json
import traceback
import requests,json


from dotenv import load_dotenv
load_dotenv()

from core.db_pickle import db_pickle_save

class DBot(discord.AutoShardedBot):
    def __init__(self, token:str, intents:Intents) -> None:
        self.token = token
        super().__init__(intents = intents)
        self.load_cogs()

    async def on_ready(self) -> None:
        await self.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Activity(name='起動中...................',type=discord.ActivityType.watching)
        )
        await self.db_get()
        print('起動しました')
        game_name = os.environ.get('GAME_NAME')
        if game_name == None:
            game_name = 'senran kagura'
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(name = game_name)
        )

    def load_cogs(self) -> None:
        for file in os.listdir("./cogs"): 
            if file.endswith(".py"): 
                cog = file[:-3] 
                self.load_extension(f"cogs.{cog}")
                print(cog + "をロードしました")

    async def db_get(self) -> None:
        # データベースへ接続
        await db_pickle_save(guilds=self.guilds)

    

        

    # 起動用の補助関数です
    def run(self) -> None:
        try:
            self.loop.run_until_complete(self.start(self.token))
        except discord.LoginFailure:
            print("Discord Tokenが不正です")
        except KeyboardInterrupt:
            print("終了します")
            self.loop.run_until_complete(self.close())
        except discord.HTTPException as e:
            traceback.print_exc()
            if e.status == 429 and os.environ.get("WEBHOOK") != None:
                main_content = {'content': 'DiscordBot 429エラー\n直ちにDockerファイルを再起動してください。'}
                headers      = {'Content-Type': 'application/json'}

                response     = requests.post(
                    url=os.environ.get("WEBHOOK"), 
                    data=json.dumps(main_content), 
                    headers=headers
                )
                
        except Exception as e:
            traceback.print_exc()
            if os.environ.get("WEBHOOK") != None:
                if os.environ.get("ADMIN_ID") != None:
                    admin_id = os.environ.get("ADMIN_ID")
                    text = f"<@{int(admin_id)}> {e}"
                else:
                    text = str(e)
                main_content = {
                    'content':text
                }
                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.post(
                    url=os.environ.get("WEBHOOK"), 
                    data=json.dumps(main_content), 
                    headers=headers
                )