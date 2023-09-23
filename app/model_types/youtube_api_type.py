from pydantic import BaseModel
from typing import List,Optional


class YouTubeChannelItemSnippetThumbnails(BaseModel):
    class YouTubeChannelItemSnippetThumbnailsDefault(BaseModel):
        """
        動画サムネイル

        param:
        height:int
            サムネイルの高さ
        url:str
            サムネイルのURL
        width:int
            サムネイルの幅
        """
        height:int
        url:str
        width:int
    class YouTubeChannelItemSnippetThumbnailsHigh(BaseModel):
        """
        動画サムネイル

        param:
        height:int
            サムネイルの高さ
        url:str
            サムネイルのURL
        width:int
            サムネイルの幅
        """
        height:int
        url:str
        width:int
    class YouTubeChannelItemSnippetThumbnailsMedium(BaseModel):
        """
        動画サムネイル

        param:
        height:int
            サムネイルの高さ
        url:str
            サムネイルのURL
        width:int
            サムネイルの幅
        """
        height:int
        url:str
        width:int

    """
    動画サムネイル

    param:
    default:YouTubeChannelItemSnippetThumbnailsDefault
        デフォルトのサムネイル
    high:YouTubeChannelItemSnippetThumbnailsHigh
        高画質のサムネイル
    medium:YouTubeChannelItemSnippetThumbnailsMedium
        中画質のサムネイル
    """
    default:YouTubeChannelItemSnippetThumbnailsDefault
    high:YouTubeChannelItemSnippetThumbnailsHigh
    medium:YouTubeChannelItemSnippetThumbnailsMedium

class YouTubeAPIError(BaseModel):
    class YouTubeAPIErrorItem(BaseModel):
        class YouTubeAPIErrorList(BaseModel):
            domain:str
            message:str
            reason:str
        code:int
        error:YouTubeAPIErrorList
        message:str

    error:YouTubeAPIErrorItem

class YouTubeChannelList(BaseModel):
    class YouTubeChannelItemList(BaseModel):
        class YouTubeChannelItemID(BaseModel):
            """
            YouTubeのチャンネルの設定に関するテーブル

            param:
            kind:str
                動画の種類
            videoId:str
                動画のid
            """
            kind:str
            videoId:str
        class YouTubeChannelItemSnippet(BaseModel):
            """
            YouTubeのチャンネルの設定に関するテーブル

            param:
            channelId:str
                チャンネルid
            channelTitle:str
                チャンネル名
            description:str
                動画の説明
            liveBroadcastContent:str
                ライブ配信の有無
            publishTime:str
                動画の投稿日時
            publishedAt:str
                動画の投稿日時
            thumbnails:YouTubeChannelItemSnippetThumbnails
                動画のサムネイル
            title:str
                動画のタイトル
            """
            channelId:str
            channelTitle:str
            description:str
            liveBroadcastContent:str
            publishTime:str
            publishedAt:str
            thumbnails:YouTubeChannelItemSnippetThumbnails
            title:str
        """
        YouTubeのチャンネルの設定に関するテーブル

        param:
        etag:str
            Etag
        id:YouTubeChannelItemID
            動画のid
        kind:str
            実行したAPIの種類
        snippet:YouTubeChannelItemSnippet
            動画の情報
        """
        etag:str
        id:YouTubeChannelItemID
        kind:str
        snippet:YouTubeChannelItemSnippet

    class YouTubeChannelPageInfo(BaseModel):
        """
        YouTubeのチャンネルの設定に関するテーブル

        param:
        totalResults:int
            取得した動画件数
        resultsPerPage:int
            上記の件数を1ページ目として残りを表示できる動画件数
        """
        totalResults:int
        resultsPerPage:int

    """
    YouTubeのチャンネルの設定に関するテーブル

    param:
    etag:str
        Etag
    items:List[YouTubeChannelItemList]
        チャンネル内の動画の情報
    kind:str
        実行したAPIの種類
    nextPageToken:str
        次のページのトークン
    pageInfo:YouTubeChannelPageInfo
        ページの情報
    regionCode:str
        地域コード
    """
    etag:str
    items:List[YouTubeChannelItemList]
    kind:str
    nextPageToken:str
    pageInfo:YouTubeChannelPageInfo
    regionCode:str

class YouTubeChannelInfo(BaseModel):
    class YouTubeChannelInfoItem(BaseModel):
        class YouTubeChannelSnippetList(BaseModel):
            customUrl:str
            description:str
            publishedAt:str
            thumbnails:YouTubeChannelItemSnippetThumbnails
            title:str
        etag:str
        id:str
        kind:str
        snippet:YouTubeChannelSnippetList
    etag:Optional[str]
    items:Optional[List[YouTubeChannelInfoItem]]
    kind:Optional[str]
    pageInfo:Optional[YouTubeChannelList.YouTubeChannelPageInfo]
    error:Optional[YouTubeAPIError]