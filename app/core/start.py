import discord
from discord.ext import tasks
from discord import Intents
import os
import datetime
import traceback
import requests,json

import aiohttp

from dotenv import load_dotenv
load_dotenv()

from core.db_pickle import db_pickle_save

class DBot(discord.AutoShardedBot):
    def __init__(self, token:str, intents:Intents) -> None:
        self.token = token
        super().__init__(intents = intents)
        self.load_cogs()

    async def on_ready(self) -> None:
        await self.db_get()
        print('起動しました')
        game_name = os.environ.get('GAME_NAME')
        if game_name == None:
            game_name = 'senran kagura'
        await self.change_presence(activity = discord.Game(name = game_name))

    def load_cogs(self) -> None:
        for file in os.listdir("./cogs"): 
            if file.endswith(".py"): 
                cog = file[:-3] 
                self.load_extension(f"cogs.{cog}")
                print(cog + "をロードしました")

    async def db_get(self) -> None:
        # データベースへ接続
        await db_pickle_save(guilds=self.guilds)

    @tasks.loop(seconds=90)
    async def signal(self) -> None:
        now = datetime.datetime.now().strftime('%H:%M')
        

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
            if e.status == 429:
                main_content = {'content': 'DiscordBot 429エラー\n直ちにDockerファイルを再起動してください。'}
                headers      = {'Content-Type': 'application/json'}

                response     = requests.post(os.environ["WEBHOOK"], json.dumps(main_content), headers=headers)
                
        except:
            traceback.print_exc()