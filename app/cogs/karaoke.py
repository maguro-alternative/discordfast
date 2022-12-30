import discord

from discord.ext import commands
from discord import Option
import asyncio
from pydub import AudioSegment
import os

try:
    from app.cogs.bin.rank import Wav_Karaoke
    from app.core.start import DBot
except:
    from cogs.bin.rank import Wav_Karaoke
    from core.start import DBot

class karaoke(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot 
        # super().__init__()

    @commands.slash_command(description = 'カラオケスタート(事前に/downloadで音源をダウンロードすること)')
    async def start_record(self,ctx:discord.ApplicationContext):

        if not bool(os.path.isfile(f'.\wave\{ctx.author.id}_music.wav')):
            await ctx.respond('音源が見つかりません')
            return

        if hasattr(ctx.guild.voice_client,'is_playing'):   # 再生中かどうか判断
            if ctx.guild.voice_client.is_playing():
                await ctx.respond("再生中です。")
                return

        if hasattr(ctx.guild.voice_client,'is_connected'):   # ボイスチャンネルに接続中かどうか判断
            if ctx.guild.voice_client.is_connected():
                await ctx.respond("ボイスチャンネルに接続中です。")
                return

        # コマンドを使用したユーザーのボイスチャンネルに接続
        if hasattr(ctx.author.voice,'channel'):
            vc = await ctx.author.voice.channel.connect()
            await ctx.respond("Recording...")
        else:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return

        karaoke = Wav_Karaoke(user_id = ctx.author.id)
        
        #source = discord.FFmpegPCMAudio(f"./wave/{ctx.author.id}_music.wav") 
        source = discord.FFmpegPCMAudio(f".\wave\{ctx.author.id}_music.wav")              # ダウンロードしたwavファイルをDiscordで流せるように変換
        trans = discord.PCMVolumeTransformer(source,volume=0.3)

        # 録音開始。mp3で帰ってくる。wavだとなぜか壊れる。
        ctx.voice_client.start_recording(discord.sinks.MP3Sink(), finished_callback, ctx)

        vc.play(trans, after=check_error)  #音源再生
        
        # 再生終了まで待つ
        #second_wait=int(await karaoke.wav_second(f"./wave/{ctx.author.id}_music.wav"))
        second_wait = await karaoke.music_wav_second()
        for i in range(0,int(second_wait)):
            if hasattr(ctx.guild.voice_client,'is_playing'):
                # print(f"\r{i}second play:{ctx.guild.voice_client.is_playing()}", end='')
                # print(f"\r{i}second", end='')
                await asyncio.sleep(1)

        ctx.voice_client.stop_recording() # 録音を停止し、直後にfinished_callbackが呼び出されます。
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
    @commands.slash_command(description = 'YouTubeから音源をダウンロード')
    async def download(
        self,
        ctx: discord.ApplicationContext,
        url: Option(str, required=True, description="urlをいれて", )
    ):

        if hasattr(ctx.guild.voice_client,'is_playing'):   # 再生中かどうか判断
            if ctx.guild.voice_client.is_playing():
                await ctx.respond("再生中です。")
                return

        karaoke = Wav_Karaoke(user_id = ctx.author.id)

        await ctx.respond("downloading...\n"+url) 
        # youtube-dlでダウンロード
        await karaoke.song_dl(url)
        # song = AudioSegment.from_file(f"./wave/{ctx.author.id}_music.wav", format="wav")
        # song.export(f"./wave/{ctx.author.id}_music.wav", format='wav')

        song = AudioSegment.from_file(f".\wave\{ctx.author.id}_music.wav", format="wav")
        song.export(f".\wave\{ctx.author.id}_music.wav", format='wav')

        await ctx.channel.send(f"<@{ctx.author.id}> ダウンロード完了! /start_record で採点します。")

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
            await asyncio.sleep(1)
        ctx.voice_client.stop_recording()

    @commands.slash_command()
    async def test_play(self,ctx:discord.ApplicationContext):
        try:
            vc = await ctx.author.voice.channel.connect()
            await ctx.respond("Recording...")
        except AttributeError:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return
        except discord.ClientException:
            await ctx.respond("入室中です。再生を開始します。")


        # source = discord.FFmpegPCMAudio(f"./wave/{ctx.author.id}_music.wav")              # ダウンロードしたwavファイルをDiscordで流せるように変換
        source = discord.FFmpegPCMAudio(f".\wave\{ctx.author.id}_music.wav")
        trans = discord.PCMVolumeTransformer(source,volume=0.3)
        vc.play(trans)  #音源再生

        karaoke = Wav_Karaoke(user_id = ctx.author.id)
        
        # 再生終了まで待つ
        second_wait = await karaoke.music_wav_second()
        for i in range(0,int(second_wait)):
            await asyncio.sleep(1)

        await ctx.voice_client.disconnect()

    @commands.slash_command()
    async def rank_scoring(self,ctx:discord.ApplicationContext):
        if not bool(os.path.isfile(f'.\wave\{ctx.author.id}_music.wav')):
            await ctx.respond('音源が見つかりません')
            return

        if hasattr(ctx.guild.voice_client,'is_playing'):   # 再生中かどうか判断
            if ctx.guild.voice_client.is_playing():
                await ctx.respond("再生中です。")
                return

        if hasattr(ctx.guild.voice_client,'is_connected'):   # ボイスチャンネルに接続中かどうか判断
            if ctx.guild.voice_client.is_connected():
                await ctx.respond("ボイスチャンネルに接続中です。")
                return

        await ctx.respond("採点中,,,")
        karaoke = Wav_Karaoke(user_id = ctx.author.id)
        wavRatio = await karaoke.voice_wav_second() / await karaoke.music_wav_second()
        
        if wavRatio>=0.5:
            # 採点結果を表示
            await ctx.channel.send(f'<@{ctx.author.id}> 点数 {await karaoke.calculate_wav_similarity()}点です！')
        else:
            await ctx.channel.send(f"<@{ctx.author.id}> 歌っている時間が短く、正常に採点出来ませんでした。")


    # 録音終了時に呼び出される関数
async def finished_callback(sink:discord.sinks.MP3Sink, ctx:discord.ApplicationContext):
    # file = open('singid.txt', 'r')  # 歌ったユーザーIDの読み込み
    # singid = int(file.read())

    # 録音したユーザーの音声を取り出す
    for user_id, audio in sink.audio_data.items():
        if user_id == ctx.author.id:     # 歌ったユーザーIDと一致した場合
            # print(type(audio.file))
            # mp3ファイルとして書き込み。その後wavファイルに変換。
            song = AudioSegment.from_file(audio.file, format="mp3")
            song.export(f'.\wave\{ctx.author.id}_voice.wav', format='wav')

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

def setup(bot:DBot):
    return bot.add_cog(karaoke(bot))