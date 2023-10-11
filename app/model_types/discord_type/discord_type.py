from pydantic import BaseModel
from typing import List,Optional,Union,Any

class DiscordUser(BaseModel):
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
        言語
    mfa_enabled         :bool

    premium_type        :int
        Nitroユーザのランク
    email               :str
        ユーザが登録しているメールアドレス
    verified            :Optional[bool]
        認証済みかどうか
    bio                 :Optional[str]
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
    locale              :Optional[str]
    mfa_enabled         :Optional[bool]
    premium_type        :Optional[int]
    email               :Optional[str]
    verified            :Optional[bool]
    bio                 :Optional[str]

class DiscordMember(BaseModel):
    """
    Discordのユーザーのサーバーでのステータス

    user        :Discordのユーザークラス
    nick        :ニックネーム
    pending     :用途不明
    flags       :こちらも用途不明
    avatar      :ユーザーのアバターハッシュ
    roles       :サーバーで割り当てられているロール
    joined_at   :参加した日付
    deaf        :スピーカーミュートしているか
    mute        :マイクミュートしているか
    """
    user        :DiscordUser
    nick        :Optional[str]
    pending     :Optional[bool]
    flags       :Optional[int]
    avatar      :Optional[str]
    roles       :Optional[List[int]]
    joined_at   :Optional[str]
    deaf        :Optional[bool]
    mute        :Optional[bool]

class DiscordRole(BaseModel):
    """
    Discordのロールのクラス

    id                  :ロールid
    name                :ロール名
    description         :ロールの説明
    permissions         :ロールに割り当てられている権限
    position            :ロールの順番
    color               :ロールの色
    hoist               :オンラインメンバーとは別に表示するか
    managed             :管理者権限?
    mentionable         :メンション可能かどうか
    icon                :サーバーにギルドアイコン機能がある場合、その画像
    unicode_emoji       :ギルドアイコン機能での絵文字
    flags               :用途不明
    permissions_new     :新たに設定する権限
    """
    id              :int
    name            :str
    description     :Optional[str]
    permissions     :int
    position        :int
    color           :int
    hoist           :bool
    managed         :bool
    mentionable     :bool
    icon            :Optional[str]
    unicode_emoji   :Optional[str]
    flags           :int
    permissions_new :int

class PermissionOverwrites(BaseModel):
    """
    Discordのチャンネルの権限のクラス
    上書きする際に使用

    id          :チャンネルのid
    type        :チャンネルのタイプ
    allow       :許可されている権限
    deny        :禁止されている権限
    allow_new   :新たなに許可する権限
    deny_new    :新たに禁止する権限
    """
    id          :int
    type        :str
    allow       :int
    deny        :int
    allow_new   :int
    deny_new    :int

class DiscordChannel(BaseModel):
    """
    Discordのチャンネルのクラス

    id                      :チャンネルid
    last_message_id         :最後に発言されたメッセージのid
    type                    :チャンネルのタイプ(0の場合、テキストチャンネル)
    name                    :チャンネル名
    position                :チャンネルの順番
    flags                   :用途不明
    parent_id               :親チャンネルのid
    bitrate                 :音声のビットレート
    user_limit              :ボイスチャンネルのユーザーの上限
    rtc_region              :音声のリージョン
    topic                   :チャンネルのトピックス
    guild_id                :サーバーid
    premission_overwrites   :新たに設定する権限
    rate_limit_per_user     :低速モードで再び発言できるまでの秒数
    nsfw                    :閲覧注意チャンネルかどうか
    """
    id                      :int
    last_message_id         :Optional[int]
    type                    :int
    name                    :str
    position                :int
    flags                   :int
    parent_id               :Optional[int]
    bitrate                 :Optional[int]
    user_limit              :Optional[int]
    rtc_region              :Optional[str]
    topic                   :Optional[str]
    guild_id                :int
    permission_overwrites   :List[PermissionOverwrites]
    rate_limit_per_user     :int
    nsfw                    :bool


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


class ThreadMetadata(BaseModel):
    """
    スレッドのメタデータ

    archived                :bool
        アーカイブされたいるかどうか
    archive_timestamp       :str
        アーカイブされた日時
    auto_archive_duration   :int
        アーカイブまでの残り秒数
    locked                  :bool
        ロックされているか
    create_timestamp        :str
        作成日時
    """
    archived                :bool
    archive_timestamp       :str
    auto_archive_duration   :int
    locked                  :bool
    create_timestamp        :str

class Threads(BaseModel):
    """
    スレッド

    id                  :int
        スレッドid
    type                :int
        チャンネルタイプ
    last_message_id     :int
        最後の投稿id
    flags               :int
        用途不明
    guild_id            :int
        サーバーid
    name                :str
        スレッド名
    parent_id           :int
        親チャンネルのid
    rate_limit_per_user :int
        レートリミット?
    bitrate             :int
        ビットレート
    user_limit          :int
        ユーザリミット
    rtc_region          :str
        リージョン
    owner_id            :int
        ?
    thread_metadata     :ThreadMetadata
        スレッドのメタデータ
    message_count       :int
        スレッドのメッセージ数
    member_count        :int
        スレッドのメンバー数
    total_message_sent  :int
        トータルでのメッセージ数
    """
    id                  :int
    type                :int
    last_message_id     :int
    flags               :int
    guild_id            :int
    name                :str
    parent_id           :int
    rate_limit_per_user :int
    bitrate             :int
    user_limit          :int
    rtc_region          :Optional[str]
    owner_id            :int
    thread_metadata     :ThreadMetadata
    message_count       :int
    member_count        :int
    total_message_sent  :int

class DiscordGuild(BaseModel):
    """
    Discordのサーバークラス
    使いません
    """
    id                              :int
    name                            :str
    icon                            :str
    description                     :Optional[str]
    home_header                     :Optional[str]
    splash                          :Optional[str]
    discovery_splash                :Optional[str]
    features                        :List[str]
    banner                          :Optional[str]
    owner_id                        :int
    application_id                  :Optional[int]
    region                          :Optional[str]
    afk_channel_id                  :Optional[int]
    afk_timeout                     :int
    system_channel_id               :Optional[int]
    system_channel_flags            :int
    widget_enabled                  :bool
    widget_channel_id               :Optional[int]
    verification_level              :int
    roles                           :List
    default_message_notifications   :int
    mfa_level                       :int
    explicit_content_filter         :int
    max_presences                   :Optional[int]
    max_members                     :int
    max_stage_video_channel_users   :Optional[int]
    max_video_channel_users         :Optional[int]
    vanity_url_code                 :Optional[str]
    premium_tier                    :int
    premium_subscription_count      :int
    preferred_locale                :str
    rules_channel_id                :Optional[int]
    safety_alerts_channel_id        :Optional[int]
    public_updates_channel_id       :Optional[int]
    hub_type                        :Optional[str]
    premium_progress_bar_enabled    :bool
    latest_onboarding_question_id   :Optional[int]
    nsfw                            :bool
    nsfw_level                      :int
    emojis                          :List
    stickers                        :List
    incidents_data                  :Any
    inventory_settings              :Any
    embed_enabled                   :bool
    embed_channel_id                :Optional[int]