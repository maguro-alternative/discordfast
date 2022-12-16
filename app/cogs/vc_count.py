import discord
from discord.ext import commands

try:
    import app.cogs.bin.activity
    from app.core.start import DBot
except:
    import cogs.bin.activity
    from core.start import DBot


class vc_count(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot      

    @commands.Cog.listener(name='on_voice_state_update')
    async def voice_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        
        if member.bot is True:
            return
        
        client = self.bot.get_channel(member.guild.system_channel.id)
        check = before.channel and after.channel and before.channel != after.channel

        if (after.channel is None or check):
            channel = discord.utils.get(member.guild.voice_channels, id=before.channel.id)
            i=len(list(channel.voice_states.keys()))
            await client.send(f"現在{i}人 <@{member.id}>が{before.channel.name}から退出しました。")

            try:
                if i==1 and before.channel.guild.voice_client.is_connected():
                    await before.channel.guild.voice_client.disconnect()
                    i=0
            except:
                print()

            if i==0:
                isum=0
                for channels in member.guild.voice_channels:
                    isum+=len(channels.voice_states.keys())
                if isum==0:
                    await client.send("@everyone 通話が終了しました。",embed=discord.Embed(title="通話終了",description=""))

        if (before.channel is None or check):
            channel = discord.utils.get(member.guild.voice_channels, id=after.channel.id)
            i=len(list(channel.voice_states.keys()))
            
            embed=None
            if i==1:
                embed = await cogs.bin.activity.callemb(after,member)
            await client.send(f"現在{i}人 @everyone <@{member.id}>が{after.channel.name} に参加しました。",embed=embed)

        if before.self_video is False and after.self_video is True:
            await client.send(f"@everyone <@{member.id}> が、{after.channel.name}でカメラ配信を始めました。",embed = await cogs.bin.activity.stream(after,member,title="カメラ配信"))
        elif after.self_video is False and before.self_video is True:
            await client.send(f"<@{member.id}> がカメラ配信を終了しました。")
        elif before.self_stream is False and after.self_stream is True:
            mst,embed = await cogs.bin.activity.activity(after,member)
            await client.send(mst,embed=embed)
        elif after.self_stream is False and before.self_stream is True:
            await client.send(f"<@{member.id}> が画面共有を終了しました。")

def setup(bot:DBot):
    return bot.add_cog(vc_count(bot))