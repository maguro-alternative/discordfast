import discord

from discord.ext import commands
from discord import Option
import os

import requests
try:
    from app.core.start import DBot
except:
    from core.start import DBot

Speaker = [ '四国めたん', '四国めたんあまあま', '四国めたんツンツン', '四国めたんセクシー',
            'ずんだもん', 'ずんだもんあまあま', 'ずんだもんツンツン', 'ずんだもんセクシー','ずんだもんささやき',
            '春日部つむぎ',
            '雨晴はう',
            '波音リツ',
            '玄野武宏',
            '白上虎太郎',
            '青山龍星',
            '冥鳴ひまり',
            '九州そら', '九州そらあまあま', '九州そらツンツン', '九州そらセクシー','九州そらささやき',
            'もち子さん',
            '剣崎雌雄'
            ]

Speaker_id = [  2,0,6,4,
                3,1,7,5,22,
                8,
                10,
                9,
                11,
                12,
                13,
                14,
                16,15,18,17,19,
                20,
                21
            ]

async def get_speaker(ctx:discord.ApplicationContext):
    return [speaker for speaker in Speaker if speaker.startswith(ctx.value)]

class voicevox(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot 

    @commands.slash_command(description="ずんだもんがしゃべってくれるぞ！！")
    async def zunda(
        self,
        ctx:discord.ApplicationContext,
        text: Option(str, required=True, description="しゃべらせる言葉",),
        speaker: Option(str, required=False, description="しゃべる人",default="ずんだもん",autocomplete=get_speaker),
        volume: Option(float, required=False, description="音量",default=1.0),
        pitch: Option(int, required=False, description="声の高さ",default=0),
        intonation: Option(int, required=False, description="イントネーション",default=1),
        speed: Option(int, required=False, description="話すスピード",default=1),
    ):
        try:
            await ctx.author.voice.channel.connect()
            await ctx.respond(f"{speaker}「 {text} 」")
        except AttributeError:
            await ctx.respond("ボイスチャンネルに入ってください。")
            return
        except discord.ClientException:
            await ctx.respond(f"{speaker}「 {text} 」")

        id=3
        key=os.environ["VOICEVOX_KEY"]

        for sp,sp_id in zip(Speaker,Speaker_id):
            if sp==speaker:
                id=sp_id
                break

        r=requests.post(
                f'https://api.su-shiki.com/v2/voicevox/audio/?key={key}&speaker={id}&pitch={pitch}&intonationScale={intonation}&speed={speed}&text={text}',
                ).content
        with open(f".\wave\zunda_{ctx.guild.id}.wav" ,mode='wb') as f: # wb でバイト型を書き込める
            f.write(r)

        source = discord.FFmpegPCMAudio(f".\wave\zunda_{ctx.guild.id}.wav")              # ダウンロードしたwavファイルをDiscordで流せるように変換
        trans = discord.PCMVolumeTransformer(source,volume=volume)
        try:
            ctx.guild.voice_client.play(trans)  #音源再生
        except :#discord.ApplicationCommandInvokeError:
            await ctx.respond(f"<@{ctx.author.id}> 同時に音声は流せません。")

    @commands.slash_command(description="ずんだもんとおさらばなのだ")
    async def stop_zunda(self,ctx:discord.ApplicationContext):
        await ctx.respond("切断しました。")
        await ctx.voice_client.disconnect()

def setup(bot:DBot):
    return bot.add_cog(voicevox(bot))