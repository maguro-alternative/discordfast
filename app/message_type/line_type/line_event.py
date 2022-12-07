from pydantic import BaseModel,validator
from typing import List,Optional,Union

class ContentProvider(BaseModel):
    type:str
    originalContentUrl:Optional[str]
    previewImageUrl:Optional[str]

class ImageSet(BaseModel):
    id:int
    total:Optional[float]
    index:Optional[float]

class Message(BaseModel):
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
    keywords:Optional[str]

class Source(BaseModel):
    groupId:Optional[str]
    userId:str
    type:str

class DeliveryContext(BaseModel):
    isRedelivery:bool

class Line_Events(BaseModel):
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
