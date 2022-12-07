import discord

from discord.ext import commands
from discord import Option
import asyncio
from pydub import AudioSegment

try:
    from app.cogs.bin import youdl
    from app.cogs.bin import rank
    from app.core.start import DBot
except:
    from cogs.bin import youdl
    from cogs.bin import rank
    from core.start import DBot

class karaoke(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot 
        # super().__init__()

    @commands.slash_command()
    async def start_record(self,ctx:discord.ApplicationContext):
        try :   # 再生中かどうか判断
            print(ctx.guild.voice_client.is_playing())
            await ctx.respond("再生中です。")
            return
        except AttributeError:
            print("record")

        # コマンドを使用したユーザーのボイスチャンネルに接続
        try:
            vc = await ctx.author.voice.channel.connect()
            await ctx.respond("Recording...")
            # コマンドを使用したユーザーのIDを書き込む
            file = open('singid.txt', 'w')
            file.write(str(ctx.author.id))
            file.close()
        except AttributeError:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return
        
        # 録音開始。mp3で帰ってくる。wavだとなぜか壊れる。
        ctx.voice_client.start_recording(discord.sinks.MP3Sink(), finished_callback, ctx)

        source = discord.FFmpegPCMAudio(f"./wave/{ctx.author.id}_music.wav")              # ダウンロードしたwavファイルをDiscordで流せるように変換
        trans = discord.PCMVolumeTransformer(source,volume=0.3)
        vc.play(trans, after=check_error)  #音源再生
        
        # 再生終了まで待つ
        second_wait=int(rank.wavsecond(f"./wave/{ctx.author.id}_music.wav"))
        for i in range(0,second_wait):
            try:
                # print(f"\r{i}second play:{ctx.guild.voice_client.is_playing()}", end='')
                print(f"\r{i}second", end='')
                await asyncio.sleep(1)
            except:
                return

        ctx.voice_client.stop_recording() # Stop the recording, finished_callback will shortly after be called
        # await ctx.respond("Stopped! 採点中,,,")
        await ctx.respond("Stopped! /rank_Scoring で採点します")
        await ctx.voice_client.disconnect()

    @commands.slash_command()
    async def stop_recording(self,ctx:discord.ApplicationContext):
        # 録音停止
        ctx.voice_client.stop_recording() 
        await ctx.respond("Stopped!")
        await ctx.voice_client.disconnect()

    # 音源ダウンロード
    @commands.slash_command()
    async def download(
        self,
        ctx: discord.ApplicationContext,
        url: Option(str, required=True, description="urlをいれて", )
    ):
        try :   # 再生中か判断
            print(ctx.guild.voice_client.is_playing())
            await ctx.respond("再生中です。")
            return
        except AttributeError:
            print("download")

        await ctx.respond("downloading...\n"+url) 
        # youtube-dlでダウンロード
        youdl.you(url,ctx.author.id)
        song = AudioSegment.from_file(f"./wave/{ctx.author.id}_music.wav", format="wav")
        song.export(f"./wave/{ctx.author.id}_music.wav", format='wav')
        await ctx.channel.send(f"<@{ctx.author.id}> ダウンロード完了! /start_record で採点します。")

    @commands.slash_command()
    async def test(self,ctx:discord.ApplicationContext):
        ctx.voice_client.start_recording(discord.sinks.MP3Sink(), finished_callback, ctx)
        await ctx.respond("test")
        print(ctx.author.voice.channel)

    @commands.slash_command()
    async def test_record(
        self,
        ctx: discord.ApplicationContext,
        wait_second: Option(int, required=True, description="録音する秒数", )
    ):
        try:
            await ctx.author.voice.channel.connect()
            await ctx.respond("Recording...")
        except AttributeError:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return
        except discord.ClientException:
            await ctx.respond("入室中です。録音を開始します。")
            ctx.voice_client.start_recording(discord.sinks.MP3Sink(), finished_callback, ctx)
        for i in range(0,wait_second):
            print(f"\r{i}second", end='')
            await asyncio.sleep(1)
        ctx.voice_client.stop_recording()

    @commands.slash_command()
    async def test_play(self,ctx:discord.ApplicationContext):
        try:
            vc = await ctx.author.voice.channel.connect()
            await ctx.respond("Recording...")
            # コマンドを使用したユーザーのIDを書き込む
            file = open('singid.txt', 'w')
            file.write(str(ctx.author.id))
            file.close()
        except AttributeError:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return
        except discord.ClientException:
            await ctx.respond("入室中です。再生を開始します。")


        source = discord.FFmpegPCMAudio(f"./wave/{ctx.author.id}_music.wav")              # ダウンロードしたwavファイルをDiscordで流せるように変換
        trans = discord.PCMVolumeTransformer(source,volume=0.3)
        vc.play(trans)  #音源再生
        
        # 再生終了まで待つ
        second_wait=int(rank.wavsecond(f"./wave/{ctx.author.id}_music.wav"))
        for i in range(0,second_wait):
            print(f"\r{i}second", end='')
            await asyncio.sleep(1)

        await ctx.voice_client.disconnect()

    @commands.slash_command()
    async def rank_scoring(self,ctx:discord.ApplicationContext):
        await ctx.respond("採点中,,,")
        wavRatio=rank.wavsecond("./wave/sample_voice.wav")/rank.wavsecond(f"./wave/{ctx.author.id}_music.wav")
        print(wavRatio)
        if wavRatio>=0.5:
            # 採点結果を表示
            await ctx.channel.send(f"<@{ctx.author.id}> 点数 "+str(rank.wavmain(ctx))+"点です！")
        else:
            await ctx.channel.send(f"<@{ctx.author.id}> 歌っている時間が短く、正常に採点出来ませんでした。")


    # 録音終了時に呼び出される関数
async def finished_callback(sink:discord.sinks.MP3Sink, ctx:discord.ApplicationContext):
    # file = open('singid.txt', 'r')  # 歌ったユーザーIDの読み込み
    # singid = int(file.read())

    # 録音したユーザーの音声を取り出す
    for user_id, audio in sink.audio_data.items():
        if user_id==int(ctx.author.id):     # 歌ったユーザーIDと一致した場合
            print(type(audio.file))
            # mp3ファイルとして書き込み。その後wavファイルに変換。
            song = AudioSegment.from_file(audio.file, format="mp3")
            song.export("./wave/sample_voice.wav", format='wav')

            """# 歌っているか判断。時間が原曲の半分以下の場合採点しない。
            wavRatio=rank.wavsecond("./wave/sample_voice.wav")/rank.wavsecond(f"./wave/{ctx.author.id}_music.wav")
            print(wavRatio)
            if wavRatio>=0.5:
                # 採点結果を表示
                await ctx.channel.send(f"<@{user_id}> 点数 "+str(rank.wavmain(ctx))+"点です！")
            else:
                await ctx.channel.send(f"<@{user_id}> 歌っている時間が短く、正常に採点出来ませんでした。")"""

def check_error(er):
    print(f'Error check: {er}')

def setup(bot):
    return bot.add_cog(karaoke(bot))