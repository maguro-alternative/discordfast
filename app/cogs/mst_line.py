import discord
from discord.ext import commands
import os
from typing import List

from dotenv import load_dotenv
load_dotenv()

try:
    from message_type.line_type.line_message import LineBotAPI
    from core.start import DBot
except:
    from app.message_type.line_type.line_message import LineBotAPI
    from app.core.start import DBot

class mst_line(commands.Cog):
    def __init__(self, bot : DBot):
        self.bot = bot

    # テストコマンド
    @commands.slash_command(description="LINEの利用状況を確認します")
    async def test_signal(self,ctx:discord.ApplicationContext):

        # 環境変数から所属しているサーバー名一覧を取得し、配列に格納
        servers_name=os.environ['SERVER_NAME']
        server_list=servers_name.split(",")
        for server_name in server_list:
            # コマンドを打ったサーバーと環境変数にあるサーバーが一致した場合、利用状況を送信
            if int(os.environ[f"{server_name}_GUILD_ID"]) == ctx.guild.id:
                await ctx.respond("LINE連携の利用状況です。")
                #day_signal([server_name],f"<@{ctx.author.id}>\nテストコマンド 現在の上限です")
                #angry_signal(PushLimit(server_name),f"<@{ctx.author.id}>\n",server_name)


    # DiscordからLINEへ
    @commands.Cog.listener(name='on_message')
    async def on_message(self, message:discord.Message):

        # メッセージがbot、閲覧注意チャンネル、ピン止め、ボイスチャンネルの場合終了
        if (message.author.bot is True or
            message.channel.nsfw is True or
            message.type == discord.MessageType.pins_add or
            message.channel.type == discord.ChannelType.voice):
            return

        # FIVE_SECONDs,FIVE_HOUR
        # ACCESS_TOKEN,GUILD_ID,TEMPLE_ID (それぞれ最低限必要な環境変数)
        bots_name=os.environ['BOTS_NAME'].split(",")

        for bot_name in bots_name:
            # メッセージが送られたサーバーを探す
            if os.environ.get(f"{bot_name}_GUILD_ID") == str(message.guild.id):
                line_bot_api = LineBotAPI(notify_token=os.environ.get(f'{bot_name}_NOTIFY_TOKEN'),line_bot_token=os.environ[f'{bot_name}_BOT_TOKEN'],line_group_id=os.environ.get(f'{bot_name}_GROUP_ID'))
                break

        # line_bot_apiが定義されなかった場合、終了
        # 主な原因はLINEグループを作成していないサーバーからのメッセージ
        if not bool('line_bot_api' in locals()):
            return

        # 送信NGのチャンネル名の場合、終了
        ng_channel = os.environ.get(f"{bot_name}_NG_CHANNEL").split(",")
        if message.channel.name in ng_channel:
            return

        # LINEに送信するメッセージのリスト
        imagelist=[]
        videolist=[]

        # テキストメッセージ
        messagetext=f"{message.channel.name}にて、{message.author.name}"

        if message.type == discord.MessageType.new_member:
            messagetext=f"{message.author.name}が参加しました。"

        if message.type == discord.MessageType.premium_guild_subscription:
            messagetext=f"{message.author.name}がサーバーブーストしました。"

        if message.type == discord.MessageType.premium_guild_tier_1:
            messagetext=f"{message.author.name}がサーバーブーストし、レベル1になりました！！！！！！！！"

        if message.type == discord.MessageType.premium_guild_tier_2:
            messagetext=f"{message.author.name}がサーバーブーストし、レベル2になりました！！！！！！！！！"

        if message.type == discord.MessageType.premium_guild_tier_3:
            messagetext=f"{message.author.name}がサーバーブーストし、レベル3になりました！！！！！！！！！！！"

        # 送付ファイルがあった場合
        if message.attachments:
            # 画像か動画であるかをチェック

            imagelist = await image_checker(message.attachments)
            videolist = await video_checker(message.attachments)

            messagetext+="が、"

            # 送信された動画と画像の数を格納
            if len(imagelist)>0:
                messagetext+=f"画像を{len(imagelist)}枚、"

            if len(videolist)>0:
                messagetext+=f"動画を{len(videolist)}個"

            # 画像と動画以外のファイルがある場合、urlを直接書き込む
            if len(imagelist) + len(videolist) < len(message.attachments):
                for attachment in message.attachments:
                    messagetext+=f"\n{attachment.url} "

            messagetext+="送信しました。"

        # メッセージ本文を書き込む
        messagetext+=f"「 {message.clean_content} 」"

        # スタンプが送付されている場合
        if message.stickers:
            # 動くスタンプは送信不可のため終了
            if message.stickers[0].url.endswith(".json"):
                return
            # 画像として送信
            else:
                imagelist = await image_checker(message.stickers)
                messagetext = f'{messagetext} スタンプ:{message.stickers[0].name}'

        if len(imagelist) > 0:
            for image in imagelist:
                await line_bot_api.push_image_notify(message=messagetext,image_url=image)

        if len(videolist) > 0:
            if hasattr(message.guild.icon,'url'):
                icon_url = message.guild.icon.url
            else:
                icon_url = message.author.display_avatar.url
            await line_bot_api.push_movie(preview_image=icon_url,movie_urls=videolist)

        if len(imagelist) + len(videolist) == 0:
            await line_bot_api.push_message_notify(message=messagetext)


async def image_checker(attachments:List[discord.Attachment]) -> List[str]:
    # 画像を識別
    image = (".jpg", ".png", ".JPG", ".PNG", ".jpeg", ".gif", ".GIF")
    image_urls = []
    for attachment in attachments:
        if attachment.url.endswith(image):
            image_urls.append(attachment.url)

    return image_urls

async def video_checker(attachments:List[discord.Attachment]) -> List[str]:
    # 動画を識別
    video = (".mp4", ".MP4", ".MOV", ".mov", ".mpg", ".avi", ".wmv")
    video_urls = []
    for attachment in attachments:
        if attachment.url.endswith(video):
            video_urls.append(attachment.url)

    return video_urls


def setup(bot:DBot):
    return bot.add_cog(mst_line(bot))