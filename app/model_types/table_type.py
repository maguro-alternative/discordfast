from pydantic import BaseModel,validator
from typing import List,Union
from uuid import UUID

class WebhookSet(BaseModel):
    """
    Webhookの送信設定を管理するテーブル

    param:
    uuid                :str
        PRIMARY KEY
        Webhookへの投稿内容を一意に識別する
        新規作成の際サーバ側で発行される
    guild_id            :int
        Discordサーバーid
    webhook_id          :int
        使用するWebhookのid
    subscription_type   :str
        Webhookと連携するサービス名
        例:niconico,YouTube
    subscription_id     :str
        Webhookと連携するアカウント
        niconicoは投稿者のナンバー、youtubeはチャンネルのid
    mention_roles       :List[int]
        投稿された場合に通知するロールid
    mention_members     :List[int]
        投稿された場合に通知するメンバーid
    ng_or_word          :List[str]
        投稿内容に指定された文字が含まれていた場合送信しない
    ng_and_word         :List[str]
        投稿内容に指定された文字がすべて含まれていた場合送信しない
    search_or_word      :List[str]
        投稿内容に指定された文字が含まれた場合、送信
    search_and_word     :List[str]
        投稿内容に指定された文字がすべて含まれた場合、送信
    mention_or_word     :List[str]
        投稿内容に指定された文字が含まれた場合メンションを付けて送信
    mention_and_word    :List[str]
        投稿内容に指定された文字がすべて含まれた場合メンションを付けて送信
    created_at          :str
        最終更新日
        %a %b %d %H:%M:%S %z %Y の形式で保存される
        例:
        Wed Jun 14 00:01:27 +0000 2023
    """
    uuid                :Union[UUID,str]
    guild_id            :str
    webhook_id          :str
    subscription_type   :str
    subscription_id     :str
    mention_roles       :List[str]
    mention_members     :List[str]
    ng_or_word          :List[str]
    ng_and_word         :List[str]
    search_or_word      :List[str]
    search_and_word     :List[str]
    mention_or_word     :List[str]
    mention_and_word    :List[str]
    created_at          :str

    @validator("uuid")
    def validate_hoge(cls, value):
        # UUIDはJSONで扱えないため文字に変換
        value_str = str(value)
        return value_str


class GuildVcChannel(BaseModel):
    """
    ボイスチャンネルの入退室管理をするテーブル
    param:
    vc_id           :int
        PRIMARY KEY
        ボイスチャンネルのid
    guild_id        :int
        Discordのサーバid
    send_signal     :bool
        入退室があった場合通知するかどうか
        Trueで通知する
    send_channel_id :int
        入退室の旨を送信するチャンネルのid
    join_bot        :bool
        Botが入退室した場合通知するか
        Trueだと通知しない
    everyone_mention:bool
        @everyoneメンションで通知するか
        Trueで通知する
    mention_role_id :List[int]
        入退室があった場合に通知するロールのid
    """
    vc_id           :int
    guild_id        :int
    send_signal     :bool
    send_channel_id :int
    join_bot        :bool
    everyone_mention:bool
    mention_role_id :List[int]

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
    ng_users        :List[str]

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
    line_user_id_permission     :List[str]
    line_role_id_permission     :List[str]
    line_bot_permission         :int
    line_bot_user_id_permission :List[str]
    line_bot_role_id_permission :List[str]
    vc_permission               :int
    vc_user_id_permission       :List[str]
    vc_role_id_permission       :List[str]
    webhook_permission          :int
    webhook_user_id_permission  :List[str]
    webhook_role_id_permission  :List[str]

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