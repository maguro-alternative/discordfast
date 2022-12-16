import discord
async def activity(after:discord.VoiceState,member:discord.Member):
    try:
        embed = discord.Embed(
            title='配信タイトル', 
            description=f'{member.activities[0].name}'
        )

        embed.set_author(
            name=member.name,  # ユーザー名
            icon_url=member.display_avatar.url  # アイコンを設定
        )

        # チャンネル名フィールド
        embed.add_field(name="チャンネル", value=after.channel.name)

        
        detail = ''
        state = ''

        # ステータス名がない場合は記述なし
        if hasattr(member.activities[0],'details'):
            detail = member.activities[0].details
        if hasattr(member.activities[0],'state'):
            state = member.activities[0].state

        # ステータスフィールド
        embed.add_field(name = detail,value = state)

        # ゲーム画像がある場合代入
        if hasattr(member.activities[0],'large_image_url'):
            embed.set_image(url=member.activities[0].large_image_url)
        
        return f"@everyone <@{member.id}> が、{after.channel.name}で「{member.activities[0].name}」の配信を始めました。",embed
    # 存在しない場合
    except IndexError:
        return f"@everyone <@{member.id}> が、{after.channel.name}で画面共有を始めました。",stream(after,member,title="画面共有")


async def callemb(after:discord.VoiceState,member:discord.Member):
    embed=discord.Embed(
        title="通話開始",
        description=f"{member.guild.name}\n<#{after.channel.id}>"
    )
    embed.set_image(url=member.guild.icon.url)
    embed.set_author(
        name=member.name,  # ユーザー名
        icon_url=member.display_avatar.url  # アイコンを設定
    )
    return embed

async def stream(after:discord.VoiceState,member:discord.Member,title:str):
    embed=discord.Embed(
        title=title,
        description=f"{member.guild.name}\n<#{after.channel.id}>"
    )
    embed.set_author(
        name=member.name,  # ユーザー名
        icon_url=member.display_avatar.url  # アイコンを設定
    )
    return embed