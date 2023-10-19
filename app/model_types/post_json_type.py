from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any
from uuid import UUID

class LinePostChannelList(BaseModel):
    """
    LINEBotの送信設定に関するテーブル

    param:
    channel_id      :int
        Discordのチャンネルのid
    line_ng_channel :bool
        送信しないチャンネルかどうか
    ng_message_type :List[str]
        送信しないメッセージの種類
    message_bot     :bool
        ボットのメッセージを送信するかどうか
    ng_users        :List[int]
        送信しないユーザのid
    """
    channel_id      :int
    line_ng_channel :bool
    ng_message_type :List[str]
    message_bot     :bool
    ng_users        :List[int]

class VcSignalChannelList(BaseModel):
    """
    ボイスチャンネルの入退室管理に関するテーブル

    param:
    vc_id           :int
        ボイスチャンネルのid
    send_signal     :bool
        送信するかどうか
    send_channel_id :int
        送信するチャンネルのid
    join_bot        :bool
        ボットの入退室を通知するかどうか
    everyone_mention:bool
        入退室時にeveryoneをメンションするかどうか
    mention_role_id :List[int]
        メンションするロールのid
    """
    vc_id           :int
    send_signal     :bool
    send_channel_id :int
    join_bot        :bool
    everyone_mention:bool
    mention_role_id :List[int]

class WebhookList(BaseModel):
    """
    Webhookの設定に関するテーブル

    param:
    uuid                :Union[UUID,str]
        Webhookのuuid
    webhook_id          :int
        Webhookのid
    subscription_type   :str
        Webhookの種類(niconico, youtube)
    subscription_id     :str
        Webhookのid(niconico, youtube)
    mention_roles       :List[int]
        メンションするロールのid
    mention_members     :List[int]
        メンションするユーザのid
    ng_or_word          :List[str]
        通知しないワード
    ng_and_word         :List[str]
        通知しないワード
    search_or_word      :List[str]
        検索するワード
    search_and_word     :List[str]
        検索するワード
    mention_or_word     :List[str]
        メンションするワード
    mention_and_word    :List[str]
        メンションするワード
    delete_flag         :Optional[bool]
        削除フラグ
    """
    uuid                :Union[UUID,str]
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
    delete_flag         :Optional[bool]

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
    default_channel_id  :int
        Discordに送信するチャンネルのid
    chenge_alert        :bool
        変更の旨をDiscordとLINEに通知するかどうか
        Trueだと送信
    """
    guild_id            :int
    default_channel_id  :int
    chenge_alert        :bool

class LinePostSuccessJson(BaseModel):
    """
    LINEBotの送信設定に関するテーブル

    param:
    guild_id        :int
        Discordサーバのid
    channel_list    :List[LinePostChannelList]
        LINEBotの送信設定に関するテーブル
    """
    guild_id    :int
    channel_list:List[LinePostChannelList]

class LineSetSuccessJson(BaseModel):
    """
    LINEBotの設定に関するテーブル

    param:
    guild_id                    :int
        Discordサーバのid
    line_notify_token           :Optional[str]
        LINEの通知用トークン
    line_bot_token              :Optional[str]
        LINEBotのトークン
    line_bot_secret             :Optional[str]
        LINEBotのシークレット
    line_group_id               :Optional[str]
        LINEのグループid
    line_client_id              :Optional[str]
        LINEのクライアントid
    line_client_secret          :Optional[str]
        LINEのクライアントシークレット
    line_notify_token_del_flag  :Optional[bool]
        LINEの通知用トークンを削除するかどうか
    line_bot_token_del_flag     :Optional[bool]
        LINEBotのトークンを削除するかどうか
    line_bot_secret_del_flag    :Optional[bool]
        LINEBotのシークレットを削除するかどうか
    line_group_id_del_flag      :Optional[bool]
        LINEのグループidを削除するかどうか
    line_client_id_del_flag     :Optional[bool]
        LINEのクライアントidを削除するかどうか
    line_client_secret_del_flag :Optional[bool]
        LINEのクライアントシークレットを削除するかどうか
    default_channel_id          :int
        Discordに送信するチャンネルのid
    debug_mode                  :bool
        デバッグモードかどうか
    """
    guild_id                    :int
    line_notify_token           :Optional[str]
    line_bot_token              :Optional[str]
    line_bot_secret             :Optional[str]
    line_group_id               :Optional[str]
    line_client_id              :Optional[str]
    line_client_secret          :Optional[str]
    line_notify_token_del_flag  :Optional[bool]
    line_bot_token_del_flag     :Optional[bool]
    line_bot_secret_del_flag    :Optional[bool]
    line_group_id_del_flag      :Optional[bool]
    line_client_id_del_flag     :Optional[bool]
    line_client_secret_del_flag :Optional[bool]
    default_channel_id          :int
    debug_mode                  :bool

class VcSignalSuccessJson(BaseModel):
    """
    ボイスチャンネルの入退室管理に関するテーブル

    param:
    guild_id            :int
        Discordサーバのid
    vc_channel_list     :List[VcSignalChannelList]
        ボイスチャンネルの入退室管理に関するテーブル
    """
    guild_id            :int
    vc_channel_list     :List[VcSignalChannelList]

class WebhookSuccessJson(BaseModel):
    """
    Webhookの設定に関するテーブル

    param:
    guild_id    :int
        Discordサーバのid
    webhook_list:List[WebhookList]
        Webhookの設定に関するテーブル
    """
    guild_id    :int
    webhook_list:List[WebhookList]