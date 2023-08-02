from pydantic import BaseModel,validator
from typing import List,Optional,Union

class ContentProvider(BaseModel):
    """
    コンテンツファイルのクラス

    type                :str
        ファイルの提供元。
    originalContentUrl  :Optional[str]
        ファイルのURL。基本的には含まれない。
    previewImageUrl     :Optional[str]
        プレビュー画像のURL。基本的には含まれない。
    """
    type:str
    originalContentUrl:Optional[str]
    previewImageUrl:Optional[str]

class ImageSet(BaseModel):
    """
    画像のクラス

    id      :int
        画像セットID。複数の画像を同時に送信した場合のみ含まれる。
    total   :Optional[float]
        同時に送信した画像の総数。
    index   :Optional[float]
        同時に送信した画像セットの中で、何番目の画像かを示す1から始まるインデックス。
        画像が届く順番が不定なので、付けられている。
    """
    id:int
    total:Optional[float]
    index:Optional[float]

class Message(BaseModel):
    """
    メッセージの内容を含むオブジェクト。
    詳細は以下の公式リファレンスを参照
    https://developers.line.biz/ja/reference/messaging-api/#message-event

    text                :Optional[str]
        メッセージのテキスト
    id                  :int
        メッセージID(公式リファレンスでは文字列だが、すべて整数なのでint)
    type                :str
        メッセージの種類(テキストか画像か)
    imageSet            :Optional[ImageSet]
        画像のセットを表すクラス。複数の画像を同時に送信した場合のみ含まれる。
    contentProvider     :Optional[ContentProvider]
        画像、動画、音声ファイルの提供元。
    duration            :Optional[int]
        動画、音声ファイルの長さ（ミリ秒）
    fileName            :Optional[str]
        ファイル名
    fileSize            :Optional[int]
        ファイルサイズ（バイト）
    title               :Optional[str]
        位置情報タイトル
    address             :Optional[str]
        住所
    latitude            :Optional[float]
        緯度
    longitude           :Optional[float]
        経度
    packageId           :Optional[str]
        スタンプのパッケージID
    stickerId           :Optional[str]
        スタンプID
    stickerResourceType :Optional[str]
        スタンプのリソースタイプ。
    keywords            :Optional[List[str]]
        スタンプを表すキーワード。
    """
    text:Optional[str]
    id:int
    type:str
    imageSet:Optional[ImageSet]
    contentProvider:Optional[ContentProvider]
    duration:Optional[int]
    fileName:Optional[str]
    fileSize:Optional[int]
    title:Optional[str]
    address:Optional[str]
    latitude:Optional[float]
    longitude:Optional[float]
    packageId:Optional[str]
    stickerId:Optional[str]
    stickerResourceType:Optional[str]
    keywords:Optional[List[str]]

class Source(BaseModel):
    """
    イベントの送信元情報を含むユーザー、グループトーク、または複数人トーククラス。

    groupId     :Optional[str]
        送信元グループトークのグループID
    userId      :str
        送信元ユーザーのID。
    type        :str
        送信元のタイプ(ユーザー、グループ)
    """
    groupId:Optional[str]
    userId:str
    type:str

class DeliveryContext(BaseModel):
    """
    Webhookイベントが再送されたものかどうかを表すクラス。

    isRedelivery:bool
        再送されたものかどうか
    """
    isRedelivery:bool

class Line_Events(BaseModel):
    """
    LINEのイベントクラス
    詳細は以下の公式リファレンスを参照
    https://developers.line.biz/ja/reference/messaging-api/#common-properties

    timestamp       :float
        イベントが送られてきた時間（ミリ秒）
    mode            :str
        チャネルの状態。
    replyToken      :str
        このイベントに対して応答メッセージを送る際に使用する応答トークン
    deliveryContext :DeliveryContext
        Webhookイベントが再送されたものかどうか。
    webhookEventId  :str
        WebhookイベントID。Webhookイベントを一意に識別するためのID。ULID形式の文字列になる。
    type            :str
        イベントのタイプを表す識別子
    message         :Message
        メッセージの内容を含むオブジェクト。
    source          :Source
        イベントの送信元情報を含むユーザー、グループトーク、または複数人トークオブジェクト。
    """
    timestamp:float
    mode:str
    replyToken:str
    deliveryContext:DeliveryContext
    webhookEventId:str
    type:str
    message:Message
    source:Source

class Line_Responses(BaseModel):
    """
    LINEのイベントクラス

    destination:str
        BotのユーザID

    events:List[Line_Events] or Line_Events
        LINE側でのイベント内容
        応答確認の場合はlistで返す。
        それ以外の場合はlistの中身を返す。
    """
    destination:str
    events:Union[List[Line_Events],Line_Events]
    @validator("events")
    def validate_hoge(cls, value):
        # 応答確認の場合
        if len(value) == 0:
            return value
        # Listの中身を返す。
        value:Optional[Line_Events]
        return value[0]
