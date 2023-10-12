from typing import List,Union,Tuple,Dict
from itertools import groupby,chain

from discord.channel import (
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
)
from discord import ChannelType

GuildChannel = Union[
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
]

async def sort_discord_channel(
    all_channel:List
) -> List:
    # 親カテゴリー格納用
    position = []

    # レスポンスのJSONからpositionでソートされたリストを作成
    sorted_channels = sorted(all_channel, key=lambda c: c['position'])

    # parent_idごとにチャンネルをまとめた辞書を作成
    channel_dict = {}

    for parent_id, group in groupby(
        sorted_channels,
        key=lambda c: c['parent_id']
    ):
        if parent_id is None:
            # 親カテゴリーのないチャンネルは、キーがNoneの辞書に追加される
            parent_id = 'None'

        # キーがまだない場合、作成(同時に値も代入)
        if channel_dict.get(str(parent_id)) == None:
            channel_dict[str(parent_id)] = list(group)
        # キーがある場合、リストを取り出して結合し代入
        else:
            listtmp:List = channel_dict[str(parent_id)]
            listtmp.extend(list(group))
            channel_dict[str(parent_id)] = listtmp
            # リストを空にする
            listtmp = list()

    # 親カテゴリーがある場合、Noneから取り出す
    for chan in channel_dict['None'][:]:
        if chan['type'] == 4:
            position.append(chan)
            channel_dict['None'].remove(chan)

    # 辞書を表示
    position_index = 0

    # 親カテゴリーの名前をリスト化
    extracted_list = [d["name"] for d in position]
    # カテゴリーに属しないチャンネルが存在する場合
    if len(channel_dict['None']) != 0:
        # 配列の長さをカテゴリー数+1にする
        all_channels = [{}] * (len(extracted_list) + 1)
    else:
        all_channels = [{}] * len(extracted_list)

    for parent_id, channel in channel_dict.items():
        # カテゴリー内にチャンネルがある場合
        if len(channel) != 0:
            for d in position:
                # カテゴリーを探索、あった場合positionを代入
                if d['id'] == channel[0]['parent_id']:
                    position_index = d['position']
                    break
        else:
            position_index = len(extracted_list)

        if len(channel) != 0:
            # 指定したリストの中身が空でない場合、空のリストを探す
            while len(all_channels[position_index]) != 0:
                if len(extracted_list) == position_index:
                    position_index -= 1
                else:
                    position_index += 1

            # 指定した位置にカテゴリー内のチャンネルを代入
            all_channels[position_index] = channel

            # 先頭がカテゴリーでない場合
            if channel[0]['parent_id'] != None:
                # 先頭にカテゴリーチャンネルを代入
                all_channels[position_index].insert(0,d)

    # list(list),[[],[]]を一つのリストにする
    all_channel_sort = list(chain.from_iterable(all_channels))

    return all_channel_sort

async def sort_channels(
    channels:List[GuildChannel]
) -> Tuple[
    Dict[str,List[GuildChannel]],
    Dict[str,GuildChannel]
]:
    """
    Discordのサーバ内のチャンネルをカテゴリーごとにソートする

    Args:
        channels (List[GuildChannel]):
        Discordのチャンネル一覧

    Returns:
        Tuple[ Dict[str,List[GuildChannel]], Dict[str,GuildChannel] ]:
        それぞれ
        カテゴリーごとにソートされたチャンネル一覧
        カテゴリー一覧
    """
    # カテゴリーチャンネルを抽出
    categorys = [
        chan
        for chan in channels
        if chan.type == ChannelType.category
    ]

    # 配列の長さをカテゴリー数+1にする(要素を入れるとappendをする際にすべてのlistに入ってしまう)
    category_list = [[] for _ in range((len(categorys) + 1))]

    category_index = dict()
    category_dict = dict()

    # カテゴリーソート
    categorys = sorted(categorys,key=lambda c:c.position)

    for i,category in enumerate(categorys):
        for chan in channels:
            # カテゴリーチャンネルがある場合
            if chan.category_id == category.id:
                category_list[i].append(chan)
            # カテゴリー所属がない場合、末尾に入れる
            elif (chan.category_id == None and
                chan not in category_list[-1] and
                chan.type != ChannelType.category):
                category_list[-1].append(chan)

        # カテゴリー内のチャンネルごとにソート
        category_list[i] = sorted(category_list[i],key=lambda cc:cc.position)
        category_dict.update({
            str(category.id) : category_list[i]
        })

        category_index.update({
            str(category.id) : category
        })

    category_dict.update({
        'None' : category_list[-1]
    })

    return category_dict,category_index