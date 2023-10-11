from core.start import DBot
import discord

from model_types.environ_conf import EnvConf

Token = EnvConf.DISCORD_BOT_TOKEN

# Bot立ち上げ
DBot(
    token=Token,
    intents=discord.Intents.all()
).run()