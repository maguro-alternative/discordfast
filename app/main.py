from core.start import DBot
import discord
import os

from dotenv import load_dotenv
load_dotenv()

from server import keep_alive

# サーバー立ち上げ
keep_alive()

Token=os.environ['TOKEN']

# Bot立ち上げ
DBot(Token,discord.Intents.all()).run()