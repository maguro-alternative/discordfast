from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any

class LineBaseRequest(BaseModel):
    """
    /group
    に送られるpostデータ

    param:
    access_token:str
        LineOAuthのトークン
        暗号化された状態で送られてくる
    guild_id    :int
        Discordのサーバーid
    sub         :str
        IDトークンの対象ユーザーID
        暗号化された状態で送られてくる
    """
    access_token:str
    guild_id    :int
    sub         :str