import discord
from discord.ext import commands

try:
    import app.cogs.bin.activity
    from app.core.start import DBot
except:
    from cogs.bin import activity
    from core.start import DBot

# ボイスチャンネルの入退室を通知
class vc_count(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot      

    @commands.Cog.listener(name='on_voice_state_update')
    async def voice_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        
        # Botの場合終了
        if member.bot is True:
            return
        
        # Discordのシステムチャンネル(welcomeメッセージが送られる場所)を取得
        client = self.bot.get_channel(member.guild.system_channel.id)
        # ボイスチャンネルを移動したかどうか
        check = before.channel and after.channel and before.channel != after.channel

        # 退出した場合
        if (after.channel is None or check):
            # ボイスチャンネルの残り人数を取得
            #channel = discord.utils.get(member.guild.voice_channels, id=before.channel.id)
            #i=len(list(channel.voice_states.keys()))
            await client.send(f"現在{len(before.channel.members)}人 <@{member.id}>が{before.channel.name}から退出しました。")

            # Botがボイスチャンネルに接続していて、それ以外の全員が退出した場合
            if hasattr(before.channel.guild.voice_client,'is_connected'):
                for bot_flag in before.channel.members:
                    # Bot以外のユーザーがいる場合、終了
                    if bot_flag.bot == False:
                        return
                # 退出
                await before.channel.guild.voice_client.disconnect()
                await client.send("@everyone 通話が終了しました。",embed=discord.Embed(title="通話終了",description=""))

            # 全員が退出した場合
            if len(before.channel.members)==0:
                isum=0
                # サーバー全体のボイスチャンネル接続ユーザーを取得
                for channels in member.guild.voice_channels:
                    isum+=len(channels.voice_states.keys())
                # 全てのチャンネルで通話しているユーザーがいない場合
                if isum==0:
                    await client.send("@everyone 通話が終了しました。",embed=discord.Embed(title="通話終了",description=""))

        # 入室の場合
        if (before.channel is None or check):
            # ボイスチャンネルの残り人数を取得
            #channel = discord.utils.get(member.guild.voice_channels, id=after.channel.id)
            #i=len(list(channel.voice_states.keys()))
            
            embed=None
            # 一人目の入室(通話開始)の場合、サーバーアイコンの埋め込みを作成
            if len(after.channel.members)==1:
                embed = await activity.callemb(after,member)
            await client.send(f"現在{len(after.channel.members)}人 @everyone <@{member.id}>が{after.channel.name} に参加しました。",embed=embed)

        # カメラ配信が始まった場合
        if before.self_video is False and after.self_video is True:
            await client.send(
                f"@everyone <@{member.id}> が、{after.channel.name}でカメラ配信を始めました。",
                embed = await activity.stream(after,member,title="カメラ配信")
            )
        elif after.self_video is False and before.self_video is True:
            await client.send(f"<@{member.id}> がカメラ配信を終了しました。")
        # 画面共有が始まった場合
        elif before.self_stream is False and after.self_stream is True:
            # プレイ中のゲームがある場合、ゲーム名を含める
            mst,embed = await activity.activity(after,member)
            await client.send(mst,embed=embed)
        elif after.self_stream is False and before.self_stream is True:
            await client.send(f"<@{member.id}> が画面共有を終了しました。")

def setup(bot:DBot):
    return bot.add_cog(vc_count(bot))