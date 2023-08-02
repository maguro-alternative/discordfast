from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any

class DiscordGuildsRequest(BaseModel):
    """
    /guildsに送られるpostデータ

    param:
    access_token:str
        DiscordOAuthのトークン
        暗号化された状態で送られてくる
    """
    access_token:str

class DiscordBaseRequest(BaseModel):
    """
    /guild
    /guild/admin
    に送られるpostデータ

    param:
    access_token:str
        DiscordOAuthのトークン
        暗号化された状態で送られてくる
    guild_id    :int
        Discordのサーバーid
    """
    access_token:str
    guild_id    :int

class DiscordAdminRequest(BaseModel):
    access_token:str
