from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any

class GuildLineChannel(BaseModel):
    """
    DiscordからLINEへの送信設定を管理するテーブル

    param:
    channel_id      :int
        PRIMARY KEY
        チャンネルid
    guild_id        :int
        Discordのサーバid
    line_ng_channel :bool
        送信NGのチャンネルかどうか
    ng_message_type :List[str]
        送信NGのメッセージタイプ
    message_bot     :bool
        Botのメッセージを送信するかどうか
    ng_users        :List[int]
        LINE側に送信しないDiscordユーザのid
    """
    channel_id      :int
    guild_id        :int
    line_ng_channel :bool
    ng_message_type :List[str]
    message_bot     :bool
    ng_users        :List[int]

class GuildSetPermission(BaseModel):
    """
    サーバごとに管理者の権限を管理するテーブル

    param:
    guild_id                    :int
        PRIMARY KEY
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

class LineBotColunm(BaseModel):
    """
    LINEBotの送信設定に関するテーブル

    param:
    guild_id            :int
        PRIMARY KEY
        Discordのサーバid
    line_notify_token   :bytes
        LINE Notifyのトークン
        暗号化されている
    line_bot_token      :bytes
        LINE Botのトークン
        暗号化されている
    line_bot_secret     :bytes
        LINE Botのシークレットキー
        暗号化されている
    line_group_id       :bytes
        メッセージを送信するLINEのグループid
        暗号化されている
    line_client_id      :bytes
        LINEログインに使用するクライアントid
        暗号化されている
    line_client_secret  :bytes
        LINEログインに使用するクライアントシークレットキー
        暗号化されている
    default_channel_id  :int
        Discordに送信するチャンネルのid
    debug_mode          :bool
        デバッグモード
        Trueにするとメッセージ送信時にグループidを返すようになる
    """
    guild_id            :int
    line_notify_token   :bytes
    line_bot_token      :bytes
    line_bot_secret     :bytes
    line_group_id       :bytes
    line_client_id      :bytes
    line_client_secret  :bytes
    default_channel_id  :int
    debug_mode          :bool