from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any

class OAuthData(BaseModel):
    """
    DiscordのOAuth2認証のデータ

    param:
    access_token    :str
        ユーザのアクセストークン
    expires_in      :int
        アクセストークンの有効期限(秒)
    refresh_token   :str
        リフレッシュトークン
    scope           :str
        許可されている権限
    token_type      :str
        トークンのタイプ
        Bearer
    """
    access_token    :str
    expires_in      :int
    refresh_token   :str
    scope           :str
    token_type      :str


class User(BaseModel):
    """
    ユーザ情報

    param:
    id                  :int
        ユーザid
    username            :str
        ユーザ名
    global_name         :Union[str,None]

    display_name        :Union[str,None]

    avatar              :str
        アバターid
    avatar_decoration   :Union[str,None]
        アバターの説明
    discriminator       :str
        ユーザ名の識別子
    public_flags        :int

    flags               :int

    banner              :Union[str,None]
        プロフィールのバナー
    banner_color        :Union[str,None]
        プロフィールのバナーのカラーコード
    accent_color        :int

    locale              :str

    mfa_enabled         :bool

    premium_type        :int
        Nitroユーザのランク
    """
    id                  :int
    username            :str
    global_name         :Union[str,None]
    display_name        :Union[str,None]
    avatar              :Optional[str]
    avatar_decoration   :Union[str,None]
    discriminator       :str
    public_flags        :int
    flags               :int
    banner              :Union[str,None]
    banner_color        :Union[str,None]
    accent_color        :Optional[int]
    locale              :str
    mfa_enabled         :bool
    premium_type        :int

class Connection(BaseModel):
    """
    Discordのアカウント連携情報

    param:
    type                :str
        連携しているサービス名(Twitter,Github)
    id                  :str
        サービスでのユーザid
    name                :str
        サービスでのユーザ名
    visibility          :int
    friend_sync         :bool
    show_activity       :bool
    verified            :bool
    two_way_link        :bool
    metadata_visibility :int
    """
    type                :str
    id                  :str
    name                :str
    visibility          :int
    friend_sync         :bool
    show_activity       :bool
    verified            :bool
    two_way_link        :bool
    metadata_visibility :int


class MatchGuild(BaseModel):
    """
    Botとユーザが所属のサーバーのクラス

    id              :int
    name            :str
    icon            :str
    owner           :bool
    permissions     :int
    features        :List
    permissions_new :int
    """
    id              :int
    name            :str
    icon            :str
    owner           :bool
    permissions     :int
    features        :List[str]
    permissions_new :int