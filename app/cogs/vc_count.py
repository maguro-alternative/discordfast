import discord
from discord.ext import commands

import aiofiles

try:
    # Botのみ起動の場合
    from app.cogs.bin import activity
    from app.core.start import DBot
except ModuleNotFoundError:
    from cogs.bin import activity
    from core.start import DBot

from dotenv import load_dotenv
load_dotenv()

import os
import io
import pickle

# ボイスチャンネルの入退室を通知
class vc_count(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot      

    @commands.Cog.listener(name='on_voice_state_update')
    async def voice_update(
        self, 
        member:discord.Member, 
        before:discord.VoiceState, 
        after:discord.VoiceState
    ):
        # 参加するボイスチャンネルのid
        if hasattr(after.channel,'id'):
            vc_channel_id = after.channel.id
        else:
            # 退出した場合のボイスチャンネルのid
            vc_channel_id = before.channel.id

        # 使用するデータベースのテーブル名
        TABLE = f'guilds_vc_signal_{member.guild.id}'

        # 読み取り
        async with aiofiles.open(
            file=f'{TABLE}.pickle',
            mode='rb'
        ) as f:
            pickled_bytes = await f.read()
            with io.BytesIO() as f:
                f.write(pickled_bytes)
                f.seek(0)
                vc_fetch = pickle.load(f)

        key_vc = [
            g 
            for g in vc_fetch 
            if int(g.get('vc_id')) == vc_channel_id
        ]

        # 通知が拒否されていた場合、終了
        if hasattr(before.channel,'id'):
            if int(key_vc[0].get('vc_id')) == before.channel.id:
                if bool(key_vc[0].get('send_signal')) == False:
                    return

        # 通知が拒否されていた場合、終了
        if hasattr(after.channel,'id'):
            if int(key_vc[0].get('vc_id')) == after.channel.id:
                if bool(key_vc[0].get('send_signal')) == False:
                    return

        # Botの場合終了
        if (bool(key_vc[0].get('join_bot')) == False and
            member.bot == True):
            return
        
        # Discordのシステムチャンネル(welcomeメッセージが送られる場所)を取得
        send_channel_id = int(key_vc[0].get('send_channel_id'))

        # ない場合システムチャンネルのidを代入
        if send_channel_id == None or send_channel_id == 0:
            if hasattr(member.guild.system_channel,'id'):
                send_channel_id = member.guild.system_channel.id
            else:
                return

        client = self.bot.get_channel(send_channel_id)

        # メンションするロールの取り出し
        mentions = [
            f"<@&{int(role_id)}> " 
            for role_id in key_vc[0].get('mention_role_id')
        ]

        # 全体メンションが有効の場合@everyoneを追加
        if (bool(key_vc[0].get('everyone_mention')) == True):
            mentions.insert(0,"@everyone")
        
        # listをstrに変換
        mention_str = " ".join(mentions)

        # ボイスチャンネルを移動したかどうか
        check = before.channel and after.channel and before.channel != after.channel

        # 退出した場合
        if (after.channel is None or check):
            # ボイスチャンネルの残り人数を取得
            await client.send(f"現在{len(before.channel.members)}人 <@{member.id}>が{before.channel.name}から退出しました。")

            # Botがボイスチャンネルに接続していて、それ以外の全員が退出した場合
            if hasattr(before.channel.guild.voice_client,'is_connected'):
                for bot_flag in before.channel.members:
                    # Bot以外のユーザーがいる場合、終了
                    if bot_flag.bot == False:
                        return
                # 退出
                await before.channel.guild.voice_client.disconnect()
                await client.send(f"{mention_str} 通話が終了しました。",embed=discord.Embed(title="通話終了",description=""))
                return

            # 全員が退出した場合
            if len(before.channel.members) == 0:
                isum = 0
                # サーバー全体のボイスチャンネル接続ユーザーを取得
                for channels in member.guild.voice_channels:
                    isum += len(channels.voice_states.keys())
                # 全てのチャンネルで通話しているユーザーがいない場合
                if isum == 0:
                    await client.send(f"{mention_str} 通話が終了しました。",embed=discord.Embed(title="通話終了",description=""))

        # 入室の場合
        if (before.channel is None or check):
            # ボイスチャンネルの残り人数を取得
            
            embed = None
            # 一人目の入室(通話開始)の場合、サーバーアイコンの埋め込みを作成
            if len(after.channel.members) == 1:
                embed = await activity.callemb(after,member)
            await client.send(f"現在{len(after.channel.members)}人 {mention_str} <@{member.id}>が{after.channel.name} に参加しました。",embed=embed)

        # カメラ配信が始まった場合
        if before.self_video is False and after.self_video is True:
            await client.send(
                f"{mention_str} <@{member.id}> が、{after.channel.name}でカメラ配信を始めました。",
                embed = await activity.stream(after,member,title="カメラ配信")
            )
        elif after.self_video is False and before.self_video is True:
            await client.send(f"<@{member.id}> がカメラ配信を終了しました。")
        # 画面共有が始まった場合
        elif before.self_stream is False and after.self_stream is True:
            # プレイ中のゲームがある場合、ゲーム名を含める
            mst,embed = await activity.activity(after,member,mention_str)
            await client.send(mst,embed=embed)
        elif after.self_stream is False and before.self_stream is True:
            await client.send(f"<@{member.id}> が画面共有を終了しました。")

def setup(bot:DBot):
    return bot.add_cog(vc_count(bot))