import aiohttp

from datetime import datetime,timezone
import feedparser

from model_types.table_type import WebhookSet
from model_types.youtube_api_type import YouTubeChannelInfo
from model_types.environ_conf import EnvConf
from core.db_create import DB

async def youtube_subsc(
    webhook:WebhookSet,
    webhook_url:str,
    table_name:str
) -> None:
    """
    YouTubeの最新動画を取得し、Webhookで投稿する

    pream:
    webhook:Dict
        webhookの情報を示す辞書型オブジェクト
    webhook_url
        webhookのurl
    table_name
        webhookの情報が登録されているテーブル名
    """
    youtube_api_key = EnvConf.YOUTUBE_API_KEY
    channel_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={webhook.subscription_id}&key={youtube_api_key}"
    new_videos_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={webhook.subscription_id}&order=date&type=video&key={youtube_api_key}&maxResults=5"

    youtube_channel_rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={webhook.subscription_id}"

    # 最終更新日を格納
    created_at = webhook.created_at
    last_upload_time = datetime.strptime(
        created_at,
        '%a %b %d %H:%M:%S %z %Y'
    )

    # rssを取得し展開
    youtube_rss = feedparser.parse(
        url_file_stream_or_string=youtube_channel_rss_url
    )

    webhook_content = {
        'content':''
    }
    text = ''

    async with aiohttp.ClientSession() as sessions:
        for i,entry in enumerate(youtube_rss.entries):
            # 動画の投稿時刻
            lastUpdate = datetime.strptime(
                entry.published,
                '%Y-%m-%dT%H:%M:%S%z'
            )
            # 最新の動画が投稿されていた場合
            if last_upload_time < lastUpdate:
                # 最終更新日を更新
                last_upload_time = lastUpdate
                if not bool('channel_info' in locals()):
                    async with sessions.get(
                        url=channel_url
                    ) as re:
                        channel:dict = await re.json()
                        channel_info = YouTubeChannelInfo(**channel)
                        if channel_info.error:
                            return
                        else:
                            # チャンネルの基本情報を取得
                            channel_item = channel_info.items[0]
                            webhook_content.update({
                                'username':channel_item.snippet.title,
                                'avatar_url':channel_item.snippet.thumbnails.high.url
                            })

                # YouTube動画のタイトル
                video_title = entry.title
                # YouTube動画のURL
                video_url = entry.link

                if len(webhook.mention_roles) > 0:
                    # メンションするロールの取り出し
                    mentions = [
                        f"<@&{int(role_id)}> "
                        for role_id in webhook.mention_roles
                    ]
                    text = " ".join(mentions) + " "

                if len(webhook.mention_members) > 0:
                    members = [
                        f"<@{int(member_id)}> "
                        for member_id in webhook.mention_members
                    ]
                    text = " ".join(members) + " "

                text += '\n' + video_title + '\n' + video_url

                webhook_content.update({
                    'content':text
                })

                # webhookに投稿
                async with sessions.post(
                    url=webhook_url,
                    data=webhook_content
                ) as re:
                    # データベースに接続し、最終更新日を更新
                    if DB.conn == None:
                        await DB.connect()
                    await DB.update_row(
                        table_name=table_name,
                        row_values={
                            'created_at':datetime.now(timezone.utc).strftime('%a %b %d %H:%M:%S %z %Y')
                        },
                        where_clause={
                            'uuid':webhook.uuid
                        }
                    )