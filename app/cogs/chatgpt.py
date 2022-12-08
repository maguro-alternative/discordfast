import requests
import json

import discord

from discord.ext import commands
from discord import Option
import os

try:
    from app.core.start import DBot
except:
    from core.start import DBot

class chatgpt(commands.Cog):
    def __init__(self, bot:DBot) -> None:
        self.bot = bot

    @commands.slash_command(description="ChatGPTに質問しよう！！")
    async def chatgpt(
        self,
        ctx:discord.ApplicationContext,
        text: Option(str, required=True, description="AIに質問したいこと",)
    ):
        r = requests.post(
            url='https://api.openai.com/v1/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + os.environ["CHATGPT"]
            },
            data=json.dumps({
                "model": "text-davinci-003",
                "prompt": text,
                "max_tokens": 4000,
                "temperature":0
            })
        )
        
        await ctx.respond(r.json()['choices'][0]['text'])

def setup(bot:DBot):
    return bot.add_cog(chatgpt(bot))
