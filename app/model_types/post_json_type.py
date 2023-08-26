from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any
from uuid import UUID

class LinePostChannelList(BaseModel):
    channel_id      :int
    line_ng_channel :bool
    ng_message_type :List[str]
    message_bot     :bool
    ng_users        :List[int]

class VcSignalChannelList(BaseModel):
    vc_id           :int
    send_signal     :bool
    send_channel_id :int
    join_bot        :bool
    everyone_mention:bool
    mention_role_id :List[int]

class WebhookList(BaseModel):
    webhook_uuid        :Union[UUID,str]
    webhook_id          :int
    subscription_type   :str
    subscription_id     :str
    mention_roles       :List[int]
    mention_members     :List[int]
    ng_or_word          :List[str]
    ng_and_word         :List[str]
    search_or_word      :List[str]
    search_and_word     :List[str]
    mention_or_word     :List[str]
    mention_and_word    :List[str]
    created_at          :str

class AdminSuccessJson(BaseModel):
    """
    サーバごとに管理者の権限を管理するテーブル

    param:
    guild_id                    :int
        Discordサーバのid
    line_permission             :int
        DiscordからLINEへの送信設定を編集できる権限コード
    line_user_id_permission     :List[int]
        DiscordからLINEへの送信設定を編集できるユーザのid
    line_role_id_permission     :List[int]
        DiscordからLINEへの送信設定を編集できるロールid
    line_bot_permission         :int
        LINEBotの設定を編集できる権限コード
    line_bot_user_id_permission :List[int]
        LINEBotの設定を編集できるユーザのid
    line_bot_role_id_permission :List[int]
        LINEBotの設定を編集できるロールid
    vc_permission               :int
        ボイスチャンネルの入退室管理を編集できる権限コード
    vc_user_id_permission       :List[int]
        ボイスチャンネルの入退室管理を編集できるユーザのid
    vc_role_id_permission       :List[int]
        ボイスチャンネルの入退室管理を編集できるロールid
    webhook_permission          :int
        Webhookを追加、編集できる権限コード
    webhook_user_id_permission  :List[int]
        Webhookを追加、編集できるユーザのid
    webhook_role_id_permission  :List[int]
        Webhookを追加、編集できるロールid
    """
    guild_id                    :int
    line_permission             :int
    line_user_id_permission     :List[int]
    line_role_id_permission     :List[int]
    line_bot_permission         :int
    line_bot_user_id_permission :List[int]
    line_bot_role_id_permission :List[int]
    vc_permission               :int
    vc_user_id_permission       :List[int]
    vc_role_id_permission       :List[int]
    webhook_permission          :int
    webhook_user_id_permission  :List[int]
    webhook_role_id_permission  :List[int]

class LineGroupSuccessJson(BaseModel):
    """
    LINEBotの送信設定に関するテーブル

    param:
    guild_id            :int
        Discordサーバのid
    access_token        :str
        DiscordOAuthのトークン
        暗号化された状態で送られてくる
    default_channel_id  :int
        Discordに送信するチャンネルのid
    change_alert        :bool
        変更の旨をDiscordとLINEに通知するかどうか
        Trueだと送信
    """
    guild_id            :int
    access_token        :str
    default_channel_id  :int
    change_alert        :bool

class LinePostSuccessJson(BaseModel):
    guild_id    :int
    access_token:str
    channel_list:List[LinePostChannelList]

class LineSetSuccessJson(BaseModel):
    guild_id            :int
    access_token        :str
    line_notify_token   :Optional[str]
    line_bot_token      :Optional[str]
    line_bot_secret     :Optional[str]
    line_group_id       :Optional[str]
    line_client_id      :Optional[str]
    line_client_secret  :Optional[str]
    default_channel_id  :int
    debug_mode          :bool

class VcSignalSuccessJson(BaseModel):
    guild_id            :int
    access_token        :str
    vc_channel_list     :List[VcSignalChannelList]

class WebhookSuccessJson(BaseModel):
    guild_id    :int
    access_token:str
    webhook_list:List[WebhookList]