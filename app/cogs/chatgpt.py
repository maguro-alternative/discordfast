import json
import aiohttp

import discord

from discord.ext import commands
from discord import Option
import os

try:
    from app.core.start import DBot
except ModuleNotFoundError:
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
        await ctx.respond(f"質問事項:{text}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
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
            ) as resp:
                r = await resp.json()
                await ctx.respond(r['choices'][0]['text'])

def setup(bot:DBot):
    return bot.add_cog(chatgpt(bot))
