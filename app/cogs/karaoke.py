import discord

from discord.ext import commands
from discord import Option
import asyncio
import os
from pydub import AudioSegment

try:
    from app.cogs.bin.rank import WavKaraoke
    from app.core.start import DBot
    from app.model_types.environ_conf import EnvConf
except ModuleNotFoundError:
    from cogs.bin.rank import WavKaraoke
    from core.start import DBot
    from model_types.environ_conf import EnvConf

# カラオケ機能
class karaoke(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot
        self.sing_user_id = 0   # 歌っているユーザーのid

    # 音源ダウンロード
    @commands.slash_command(description = 'YouTubeから音源をダウンロード')
    async def download(
        self,
        ctx: discord.ApplicationContext,
        url: Option(str, required=True, description="urlをいれて", )
    ):

        if hasattr(ctx.guild.voice_client,'is_playing'):   # 再生中かどうか判断
            if ctx.guild.voice_client.is_playing():
                if self.sing_user_id == ctx.author.id:
                    await ctx.respond("再生中です。")
                    return

        karaoke_ongen = WavKaraoke(user_id = ctx.author.id)

        await ctx.respond("downloading...\n"+url)
        # youtube-dlでダウンロード
        try:
            await karaoke_ongen.yt_song_dl(url)
        except:
            await ctx.channel.send(f'<@{ctx.author.id}> 403エラー もう一度ダウンロードし直してください。')

        await ctx.channel.send(f"<@{ctx.author.id}> ダウンロード完了! /start_record で採点します。")



    @commands.slash_command(description = 'カラオケスタート(事前に/downloadで音源をダウンロードすること)')
    async def start_record(
        self,
        ctx:discord.ApplicationContext,
        volume: Option(float, required=False, description="音量", default=0.3),
    ):

        file_path_bool = os.path.isfile(f'.\wave\{ctx.author.id}_music.wav')
        playing_bool = hasattr(ctx.guild.voice_client,'is_playing')
        connected_bool = hasattr(ctx.guild.voice_client,'is_connected')

        if not bool(file_path_bool):
            await ctx.respond('音源が見つかりません')
            return

        if playing_bool:   # 再生中かどうか判断
            if ctx.guild.voice_client.is_playing():
                await ctx.respond("再生中です。")
                return

        # コマンドを使用したユーザーのボイスチャンネルに接続
        if hasattr(ctx.author.voice,'channel'):
            if connected_bool:
                if ctx.author.voice.channel.is_connected():
                    await ctx.respond("ボイスチャンネルに接続中です。録音中...")
            else:
                vc = await ctx.author.voice.channel.connect()
                await ctx.respond("録音中...")
        else:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return

        karaoke = WavKaraoke(user_id = ctx.author.id)
        self.sing_user_id = ctx.author.id

        #source = discord.FFmpegPCMAudio(f"./wave/{ctx.author.id}_music.wav")
        source = discord.FFmpegPCMAudio(f".\wave\{ctx.author.id}_music.wav")              # ダウンロードしたwavファイルをDiscordで流せるように変換
        trans = discord.PCMVolumeTransformer(source, volume = volume)

        # 録音開始。mp3で帰ってくる。wavだとなぜか壊れる。
        ctx.voice_client.start_recording(discord.sinks.MP3Sink(), finished_callback, ctx)

        vc.play(trans, after=check_error)  #音源再生

        # 再生終了まで待つ
        second_wait = await karaoke.music_wav_second()
        for i in range(0,int(second_wait)):
            if hasattr(ctx.guild.voice_client,'is_playing'):
                await asyncio.sleep(1)

        ctx.voice_client.stop_recording() # 録音を停止し、直後にfinished_callbackが呼び出されます。

        await ctx.respond("録音終了! /rank_Scoring で採点します")
        await ctx.voice_client.disconnect()

        game_name = EnvConf.GAME_NAME
        if game_name == None:
            game_name = 'senran kagura'

        await self.bot.change_presence(activity = discord.Game(name = game_name))


    @commands.slash_command(description = '音源と音声を比較し、100点満点で採点します。')
    async def rank_scoring(self,ctx:discord.ApplicationContext):
        if not bool(os.path.isfile(f'.\wave\{ctx.author.id}_music.wav')):
            await ctx.respond('音源が見つかりません')
            return

        if hasattr(ctx.guild.voice_client,'is_playing'):   # 再生中かどうか判断
            if ctx.guild.voice_client.is_playing() and self.sing_user_id == ctx.author.id:
                await ctx.respond("再生中です。")
                return

        await ctx.respond("採点中,,,")
        karaoke = WavKaraoke(user_id = ctx.author.id)

        await karaoke.limit_wav_duration()
        # 原曲と音声の長さを除算し、歌っているか判断
        wavRatio = await karaoke.voice_wav_second() / await karaoke.music_wav_second()

        # 5割以下の場合は採点しない
        if wavRatio>=0.5:
            # 採点結果を表示
            await ctx.channel.send(f'<@{ctx.author.id}> 点数 {await karaoke.calculate_wav_similarity()}点です！')
        else:
            await ctx.channel.send(f"<@{ctx.author.id}> 歌っている時間が短く、正常に採点出来ませんでした。")



    @commands.slash_command(description = '録音を停止します。')
    async def stop_recording(self,ctx:discord.ApplicationContext):
        # 録音停止
        ctx.voice_client.stop_recording()
        await ctx.respond("録音停止!")
        await ctx.voice_client.disconnect()

    @commands.slash_command(description = '指定した秒数録音を行い、mp3でファイルを返します。')
    async def test_record(
        self,
        ctx: discord.ApplicationContext,
        wait_second: Option(int, required=True, description="録音する秒数", )
    ):
        if hasattr(ctx.author.voice,'channel'):
            if hasattr(ctx.guild.voice_client,'is_connected'):   # ボイスチャンネルに接続中かどうか判断
                if ctx.guild.voice_client.is_connected():
                    await ctx.respond("入室中です。録音を開始します。")
            else:
                await ctx.author.voice.channel.connect()
                await ctx.respond("録音中...")
        else:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return

        ctx.voice_client.start_recording(discord.sinks.MP3Sink(), record_callback, ctx)
        for i in range(0,wait_second):
            await asyncio.sleep(1)
        ctx.voice_client.stop_recording()

    @commands.slash_command(description = '音源を再生します。')
    async def test_play(
        self,
        ctx: discord.ApplicationContext,
        user_voice: Option(bool, required = False, description = '録音した音声を流すかどうか', default = False),
        volume: Option(float, required=False, description="音量",default=0.3),
    ):
        if not bool(os.path.isfile(f'.\wave\{ctx.author.id}_music.wav')):
            await ctx.respond('音源が見つかりません')
            return
        if hasattr(ctx.author.voice,'channel'):
            if hasattr(ctx.guild.voice_client,'is_connected'):   # ボイスチャンネルに接続中かどうか判断
                if ctx.guild.voice_client.is_connected():
                    await ctx.respond("入室中です。再生を開始します。")
                    vc = ctx.guild.voice_client
            else:
                vc = await ctx.author.voice.channel.connect()
                await ctx.respond("再生中...")
        else:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return

        karaoke = WavKaraoke(user_id = ctx.author.id)

        # source = discord.FFmpegPCMAudio(f"./wave/{ctx.author.id}_music.wav")              # ダウンロードしたwavファイルをDiscordで流せるように変換
        if user_voice:
            if not bool(os.path.isfile(f'.\wave\{ctx.author.id}_voice.wav')):
                await ctx.respond('音源が見つかりません')
                return
            source = discord.FFmpegPCMAudio(f".\wave\{ctx.author.id}_voice.wav")
            second_wait = await karaoke.voice_wav_second()
        else:
            source = discord.FFmpegPCMAudio(f".\wave\{ctx.author.id}_music.wav")
            second_wait = await karaoke.music_wav_second()

        trans = discord.PCMVolumeTransformer(source,volume = volume)
        vc.play(trans)  #音源再生

        # 再生終了まで待つ
        for i in range(0, int(second_wait)):
            await asyncio.sleep(1)

        await ctx.voice_client.disconnect()
        await ctx.channel.send('再生終了!')



# 録音終了時に呼び出される関数
async def finished_callback(sink:discord.sinks.MP3Sink, ctx:discord.ApplicationContext):

    # 録音したユーザーの音声を取り出す
    for user_id, audio in sink.audio_data.items():
        if user_id == ctx.author.id:# 歌ったユーザーIDと一致した場合
            # mp3ファイルとして書き込み。その後wavファイルに変換。
            song = AudioSegment.from_file(audio.file, format="mp3")
            song.export(f'.\wave\{ctx.author.id}_voice.wav', format='wav')

async def record_callback(sink:discord.sinks.MP3Sink, ctx:discord.ApplicationContext):
    # 録音したユーザーの音声を取り出す
    recorded_users = [
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    # discordにファイル形式で送信。拡張子はmp3。
    files = [
        discord.File(audio.file, f"{user_id}.{sink.encoding}")
        for user_id, audio in sink.audio_data.items()
    ]
    await ctx.channel.send(f"録音終了! 音声ファイルはこちら! {', '.join(recorded_users)}.", files=files)

def check_error(er):
    print(f'Error check: {er}')

def setup(bot:DBot):
    return bot.add_cog(karaoke(bot))