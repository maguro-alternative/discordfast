import discord
def activity(after,member:discord.Member):
    try:
        embed = discord.Embed(
            title='配信タイトル', 
            description=f'{member.activities[0].name}'
        )

        embed.set_author(
            name=member.name,  # ユーザー名
            icon_url=member.display_avatar.url  # アイコンを設定
        )

        embed.add_field(name="チャンネル", value=after.channel.name)

        try:
            embed.add_field(name=member.activities[0].details,
                            value=member.activities[0].state)
            embed.set_image(url=member.activities[0].large_image_url)
        except IndexError:
            print("IndexError....")
        except AttributeError:
            try:
                embed.add_field(name=member.activities[0].details,
                                value=member.activities[0].state)
            except AttributeError:
                print("AttributeError.....")
        return f"@everyone <@{member.id}> が、{after.channel.name}で「{member.activities[0].name}」の配信を始めました。",embed
    # 存在しない場合
    except IndexError:
        return f"@everyone <@{member.id}> が、{after.channel.name}で画面共有を始めました。",stream(after,member,title="画面共有")


def callemb(after,member:discord.Member):
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

def stream(after,member:discord.Member,title):
    embed=discord.Embed(
        title=title,
        description=f"{member.guild.name}\n<#{after.channel.id}>"
    )
    embed.set_author(
        name=member.name,  # ユーザー名
        icon_url=member.display_avatar.url  # アイコンを設定
    )
    return embed