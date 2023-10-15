import discord
from discord.ext import commands
import os
from typing import List,Tuple,Union
import re

import subprocess
from functools import partial

import io
import asyncio
import aiofiles

from pkg.crypt import decrypt_password
try:
    from model_types.line_type.line_message import LineBotAPI,VoiceFile
    from model_types.table_type import GuildLineChannel,LineBotColunm
    from model_types.environ_conf import EnvConf
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.model_types.line_type.line_message import LineBotAPI,VoiceFile
    from app.model_types.table_type import GuildLineChannel,LineBotColunm
    from app.model_types.environ_conf import EnvConf
    from app.core.start import DBot
    from app.core.db_create import DB

ENCRYPTED_KEY = EnvConf.ENCRYPTED_KEY

class mst_line(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot

    # DiscordからLINEへ
    @commands.Cog.listener(name='on_message')
    async def on_message(self, message:discord.Message):

        # 使用するデータベースのテーブル名
        TABLE = f'guilds_line_channel'

        if DB.conn == None:
            await DB.connect()

        # 読み取り
        #async with asyncpg.create_pool(DB.dburl):
        line_bot_tabel_fetch:List[dict] = await DB.select_rows(
            table_name='line_bot',
            columns=[],
            where_clause={
                'guild_id':message.guild.id
            }
        )
        line_tabel_fetch:List[dict] = await DB.select_rows(
            table_name=TABLE,
            columns=[],
            where_clause={
                'channel_id':message.channel.id
            }
        )

        # テーブルが存在しない場合、作成
        if len(line_tabel_fetch) == 0:
            await DB.insert_row(
                table_name=TABLE,
                row_values={
                    'channel_id':message.channel.id,
                    'guild_id':message.guild.id,
                    'line_ng_channel':False,
                    'message_bot':False,
                    'ng_message_type':[],
                    'ng_users':[]
                }
            )
            # 再度読み取り
            line_tabel_fetch:List[dict] = await DB.select_rows(
                table_name=TABLE,
                columns=[],
                where_clause={
                    'channel_id':message.channel.id
                }
            )

        line_bot_fetch = LineBotColunm(**line_bot_tabel_fetch[0])
        line_fetch = GuildLineChannel(**line_tabel_fetch[0])

        bot_message = False
        ng_channel = False

        # メッセージがbotの場合
        if (line_fetch.message_bot and message.author.bot):
            # 禁止されていた場合終了
            bot_message = True

        # 送信が禁止されていた場合終了
        if line_fetch.line_ng_channel:
            ng_channel = True

        # ピン止め、ボイスチャンネルの場合終了
        # 送信NGのチャンネル名の場合、終了
        if (bot_message or ng_channel or
            str(message.type) in line_fetch.ng_message_type or
            message.author.id in line_fetch.ng_users):
            return

        line_notify_token:str = await decrypt_password(encrypted_password=bytes(line_bot_fetch.line_notify_token))
        line_bot_token:str = await decrypt_password(encrypted_password=bytes(line_bot_fetch.line_bot_token))
        line_group_id:str = await decrypt_password(encrypted_password=bytes(line_bot_fetch.line_group_id))

        # いずれかの項目が未入力の場合、終了
        if len(line_bot_token) == 0 or len(line_notify_token) == 0 or len(line_group_id) == 0:
            print('LINEトークンに未入力項目あり')
            return
        else:
            line_bot_api = LineBotAPI(
                notify_token=line_notify_token,
                line_bot_token=line_bot_token,
                line_group_id=line_group_id
            )

        # line_bot_apiが定義されなかった場合、終了
        # 主な原因はLINEグループを作成していないサーバーからのメッセージ
        if not bool('line_bot_api' in locals()):
            return

        # LINEに送信する動画、画像、音声ファイルのリスト
        imagelist = []
        videolist = []
        voicelist = []

        # ユーザーネームの空白文字を削除
        user_name = re.sub("[\u3000 \t]", "",message.author.name)

        messageTexts = {
            discord.MessageType.new_member: f"{user_name}が参加しました。",
            discord.MessageType.premium_guild_subscription: f"{user_name}がサーバーブーストしました。",
            discord.MessageType.premium_guild_tier_1: f"{user_name}がサーバーブーストし、レベル1になりました！！！！！！！！",
            discord.MessageType.premium_guild_tier_2: f"{user_name}がサーバーブーストし、レベル2になりました！！！！！！！！！",
            discord.MessageType.premium_guild_tier_3: f"{user_name}がサーバーブーストし、レベル3になりました！！！！！！！！！！！"
        }
        messagetext = messageTexts.get(message.type, f"{message.channel.name}にて、{user_name}")

        # 送付ファイルがあった場合
        if message.attachments:
            videolist = list()
            voicelist = list()

            # Bot側の送信上限を計算
            group_user_count = await line_bot_api.group_user_count()
            message_push_count = await line_bot_api.totalpush()
            message_push_limit = await line_bot_api.pushlimit()

            push_limit = message_push_limit.value - message_push_count.totalUsage
            # ファイルを送信できる場合
            if push_limit >= group_user_count.count:
                videolist, message.attachments = await video_checker(message.attachments)
                voicelist, message.attachments = await voice_checker(message.attachments,message)

            # 画像か動画であるかをチェック
            imagelist, message.attachments = await image_checker(message.attachments)

            messagetext += "が、"

            # 送信された動画と画像の数を格納
            if len(imagelist) > 0:
                messagetext += f"画像を{len(imagelist)}枚、"

            if len(videolist) > 0:
                messagetext += f"動画を{len(videolist)}個、"

            if len(voicelist) > 0:
                messagetext += f"音声を{len(voicelist)}個、"

            # 画像と動画以外のファイルがある場合、urlを直接書き込む
            if message.attachments:
                for attachment in message.attachments:
                    messagetext += f"\n{attachment.url} "

            messagetext += "送信しました。"

        # メッセージ本文を書き込む
        messagetext += f"「 {message.clean_content} 」"

        # スタンプが送付されている場合
        if message.stickers:
            # 動くスタンプは送信不可のため終了
            if message.stickers[0].url.endswith(".json"):
                return
            # 画像として送信
            else:
                messagetext = f'{messagetext} スタンプ:{message.stickers[0].name}'
                imagelist, message.stickers = await image_checker(message.stickers)

        # 画像を一個ずつNotifyで送信
        if len(imagelist) > 0:
            for image in imagelist:
                await line_bot_api.push_image_notify(message=messagetext,image_url=image)

        # 動画を送信
        if len(videolist) > 0:
            if hasattr(message.guild.icon,'url'):
                icon_url = message.guild.icon.url
            else:
                icon_url = message.author.display_avatar.url

            await line_bot_api.push_message_notify(message=messagetext)
            await line_bot_api.push_movie(preview_image=icon_url,movie_urls=videolist)

        # 音声を送信
        if len(voicelist) > 0:
            await line_bot_api.push_message_notify(message=messagetext)
            await line_bot_api.push_voice(VoiceFile=voicelist)

        # ファイルなしの場合、テキストを送信
        if len(imagelist) + len(videolist) + len(voicelist) == 0:
            await line_bot_api.push_message_notify(message=messagetext)


    # テストコマンド
    @commands.slash_command(description="LINEの利用状況を確認します")
    async def test_signal(self,ctx:discord.ApplicationContext):

        if DB.conn == None:
            await DB.connect()

        # 読み取り
        line_bot_tabel_fetch:List[dict] = await DB.select_rows(
            table_name='line_bot',
            columns=[],
            where_clause={
                'guild_id':ctx.guild.id
            }
        )

        if len(line_bot_tabel_fetch) == 0:
            await ctx.respond('LINE Notfiyが登録されていません。')
            return

        bot_info = LineBotColunm(**line_bot_tabel_fetch[0])

        await ctx.respond("LINE連携の利用状況です。")

        line_notify_token:str = await decrypt_password(encrypted_password=bot_info.line_notify_token)
        line_bot_token:str = await decrypt_password(encrypted_password=bot_info.line_bot_token)
        line_group_id:str = await decrypt_password(encrypted_password=bot_info.line_group_id)

        # いずれかの項目が未入力の場合、終了
        if len(line_bot_token) == 0 or len(line_notify_token) == 0 or len(line_group_id) == 0:
            await ctx.respond('LINEが登録されていません。')

        line_signal = LineBotAPI(
            notify_token = line_notify_token,
            line_bot_token = line_bot_token,
            line_group_id = line_group_id
        )

        states = await line_signal.notify_status()

        pushlimit = await line_signal.pushlimit()
        totalpush = await line_signal.totalpush()
        member_count = await line_signal.group_or_friend_count()

        embed = discord.Embed(
            title = ctx.guild.name,
            description = f"""
            一か月のメッセージ送信上限(基本1000,23年6月以降は200):
                **{pushlimit}**\n
            今月の送信数:
                **{totalpush.totalUsage}**\n
            友達、グループ人数:
                **{member_count}**\n
            1時間当たりのメッセージ送信上限(1000):
                **{states.rate_limit}**\n
            1時間当たりの残りメッセージ送信数:
                **{states.rate_remaining}**\n
            1時間当たりの画像送信上限数(50):
                **{states.image_limit}**\n
            1時間当たりの残り画像送信数:
                **{states.image_remaining}**
            """
        )

        await ctx.channel.send(embed = embed)
        return

# 画像を識別
async def image_checker(
    attachments:List[discord.Attachment]
) -> Tuple[
    List[str],
    Union[List[discord.Attachment],List[discord.StickerItem]]
]:
    """
    Discordの送付ファイルから、画像を抜き出す。
    引数:      attachments:    Discordの送付ファイル
    戻り値:
        image_urls:     画像かスタンプのurlリスト
        attachments:    画像を抜き出したDiscordの送付ファイル
    """
    images = (".jpg", ".png", ".JPG", ".PNG", ".jpeg", ".gif", ".GIF")
    image_urls = []
    for attachment in attachments[:]:
        # 画像があった場合、urlを画像のリストに追加し、送付ファイルのリストから削除
        for image in images:
            if attachment.url.find(image) > 0:
                image_urls.append(attachment.url)
                attachments.remove(attachment)

    return image_urls, attachments

# 動画を識別
async def video_checker(
    attachments:List[discord.Attachment]
) -> Tuple[
    List[str],
    List[discord.Attachment]
]:
    """
    Discordの送付ファイルから、動画を抜き出す。
    引数:      attachments:    Discordの送付ファイル
    戻り値:
        video_urls:     動画のurlリスト
        attachments:    動画を抜き出したDiscordの送付ファイル
    """
    videos = (".mp4", ".MP4", ".MOV", ".mov", ".mpg", ".avi", ".wmv")
    video_urls = []
    for attachment in attachments[:]:
        # 動画があった場合、urlを動画のリストに追加し、送付ファイルのリストから削除
        for video in videos:
            if attachment.url.find(video) > 0:
                video_urls.append(attachment.url)
                attachments.remove(attachment)

    return video_urls, attachments

# 音声を識別
async def voice_checker(
    attachments:List[discord.Attachment],
    message:discord.Message
) -> Tuple[
    List[VoiceFile],
    List[discord.Attachment]
]:
    """
    Discordの送付ファイルから、音声を抜き出す。
    m4a以外のファイルは、ffmpegで変換しDiscordに送信する。
    引数:      attachments:    Discordの送付ファイル
    戻り値:
        video_urls:     音声のurlリスト
        attachments:    音声を抜き出したDiscordの送付ファイル
    """
    voices = (".wav",".mp3",".flac",".aif",".m4a",".oga",".ogg")
    VoiceFiles = []
    loop = asyncio.get_event_loop()
    for attachment in attachments[:]:
        # 動画があった場合、urlを動画のリストに追加し、送付ファイルのリストから削除
        for voice in voices:
            if attachment.url.find(voice) > 0:
                # 音声ファイルをダウンロードする
                await attachment.save(attachment.filename)

                # m4aの場合はそのまま格納
                if attachment.url.find('.m4a') > 0:
                    voice_url = attachment.url
                    attachments.remove(attachment)
                else:
                    # ffmpegを使用して音声ファイルをm4aに変換する
                    output_filename = f"{os.path.splitext(attachment.filename)[0]}.m4a"
                    await loop.run_in_executor(
                        None,
                        partial(
                            subprocess.run,['ffmpeg', '-i', attachment.filename, output_filename],
                            check=True
                        )
                    )

                    # aiofilesで非同期でファイルを開く
                    async with aiofiles.open(output_filename, 'rb') as f:
                        m4a_data = await f.read()
                        # Discordにファイルを送信する
                        m4a_file = discord.File(
                            fp=io.BytesIO(m4a_data),
                            filename=output_filename
                        )
                        m4a_file_message = await message.channel.send(f"m4aファイルに変換します。: {attachment.filename} -> {output_filename}", file=m4a_file)

                    voice_url = m4a_file_message.attachments[0].url
                    # 変換したoggファイルのurl
                    attachments.remove(attachment)

                # m4aファイルの秒数を計算
                cmd = f"ffprobe -hide_banner {output_filename}.m4a -show_entries format=duration"
                process = await loop.run_in_executor(
                    None,
                    partial(
                        subprocess.run,cmd.split(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                )
                stdout_result = process.stdout.decode()
                match = re.search(r'(\d+\.\d+)', stdout_result)
                sound_second = float(match.group(1))

                VoiceFiles.append(VoiceFile(
                    url=voice_url,
                    second=sound_second
                ))

                # 変換したファイルを削除する
                os.remove(output_filename)
                os.remove(attachment.filename)

    return VoiceFiles, attachments

def setup(bot:DBot):
    return bot.add_cog(mst_line(bot))