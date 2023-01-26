import discord
from discord.ext import commands
import os
from typing import List,Tuple,Union
import re

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
                line_bot_api = LineBotAPI(
                    notify_token = os.environ.get(f'{bot_name}_NOTIFY_TOKEN'),
                    line_bot_token = os.environ[f'{bot_name}_BOT_TOKEN'],
                    line_group_id = os.environ.get(f'{bot_name}_GROUP_ID')
                )
                break

        # line_bot_apiが定義されなかった場合、終了
        # 主な原因はLINEグループを作成していないサーバーからのメッセージ
        if not bool('line_bot_api' in locals()):
            return

        # 送信NGのチャンネル名の場合、終了
        ng_channel = os.environ.get(f"{bot_name}_NG_CHANNEL").split(",")
        if message.channel.name in ng_channel:
            return

        # LINEに送信する動画、画像ファイルのリスト
        imagelist = []
        videolist = []

        # ユーザーネームの空白文字を削除
        # message.author.name = message.author.name.replace("[\u3000 \t]", "", regex=True)
        message.author.name = re.sub("[\u3000 \t]", "",message.author.name)


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
            imagelist, message.attachments = await image_checker(message.attachments)
            videolist, message.attachments = await video_checker(message.attachments)

            messagetext+="が、"

            # 送信された動画と画像の数を格納
            if len(imagelist)>0:
                messagetext += f"画像を{len(imagelist)}枚、"

            if len(videolist)>0:
                messagetext += f"動画を{len(videolist)}個"

            # 画像と動画以外のファイルがある場合、urlを直接書き込む
            if message.attachments:
                for attachment in message.attachments:
                    messagetext += f"\n{attachment.url} "

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

        # ファイルなしの場合、テキストを送信
        if len(imagelist) + len(videolist) == 0:
            await line_bot_api.push_message_notify(message=messagetext)


    # テストコマンド
    @commands.slash_command(description="LINEの利用状況を確認します")
    async def test_signal(self,ctx:discord.ApplicationContext):

        # 環境変数から所属しているサーバー名一覧を取得し、配列に格納
        servers_name = os.environ['BOTS_NAME']
        server_list = servers_name.split(",")
        for server_name in server_list:
            # コマンドを打ったサーバーと環境変数にあるサーバーが一致した場合、利用状況を送信
            if int(os.environ[f"{server_name}_GUILD_ID"]) == ctx.guild.id:

                if os.environ.get(f'{server_name}_NOTIFY_TOKEN') == None:
                    await ctx.respond('LINE Notfiyが登録されていません。')
                    return

                await ctx.respond("LINE連携の利用状況です。")

                line_signal = LineBotAPI(
                    notify_token = os.environ.get(f'{server_name}_NOTIFY_TOKEN'),
                    line_bot_token = os.environ[f'{server_name}_BOT_TOKEN'],
                    line_group_id = os.environ.get(f'{server_name}_GROUP_ID')
                )

                embed = discord.Embed(
                    title = ctx.guild.name,
                    description = f"""
                    一か月のメッセージ送信上限(基本1000,23年6月以降は200):
                        **{await line_signal.pushlimit()}**\n
                    今月の送信数:
                        **{await line_signal.totalpush()}**\n
                    友達、グループ人数:
                        **{await line_signal.friend()}**\n
                    1時間当たりのメッセージ送信上限(1000):
                        **{await line_signal.rate_limit()}**\n
                    1時間当たりの残りメッセージ送信数:
                        **{await line_signal.rate_remaining()}**\n
                    1時間当たりの画像送信上限数(50):
                        **{await line_signal.rate_image_limit()}**\n
                    1時間当たりの残り画像送信数:
                        **{await line_signal.rate_image_remaining()}**
                    """
                )

                await ctx.channel.send(embed = embed)
                return
                
        await ctx.respond('LINEが登録されていません。')

# 画像を識別
async def image_checker(attachments:List[discord.Attachment]) -> Tuple[List[str],Union[List[discord.Attachment],List[discord.StickerItem]]]:
    """
    Discordの送付ファイルから、画像を抜き出す。
    引数:      attachments:    Discordの送付ファイル
    戻り値:    image_urls:     画像かスタンプのurlリスト
               attachments:    画像を抜き出したDiscordの送付ファイル
    """
    image = (".jpg", ".png", ".JPG", ".PNG", ".jpeg", ".gif", ".GIF")
    image_urls = []
    for attachment in attachments[:]:
        # 画像があった場合、urlを画像のリストに追加し、送付ファイルのリストから削除
        if attachment.url.endswith(image):
            image_urls.append(attachment.url)
            attachments.remove(attachment)

    return image_urls, attachments

# 動画を識別
async def video_checker(attachments:List[discord.Attachment]) -> Tuple[List[str],List[discord.Attachment]]:
    """
    Discordの送付ファイルから、動画を抜き出す。
    引数:      attachments:    Discordの送付ファイル
    戻り値:    video_urls:     動画のurlリスト
               attachments:    動画を抜き出したDiscordの送付ファイル
    """
    video = (".mp4", ".MP4", ".MOV", ".mov", ".mpg", ".avi", ".wmv")
    video_urls = []
    for attachment in attachments[:]:
        # 動画があった場合、urlを動画のリストに追加し、送付ファイルのリストから削除
        if attachment.url.endswith(video):
            video_urls.append(attachment.url)
            attachments.remove(attachment)

    return video_urls, attachments


def setup(bot:DBot):
    return bot.add_cog(mst_line(bot))