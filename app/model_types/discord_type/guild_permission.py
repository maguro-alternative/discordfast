class Permission:
    def __init__(self) -> None:
        """
        このクラスは、Discordの権限を表すために使用されます。

        各権限は、クラスの属性として定義されています。
        それぞれの属性には、TrueまたはFalseのブール値が割り当てられています。

        administrator:              管理者権限を持っているかどうか
        create_instant_invite:      サーバーに招待リンクを作成できるかどうか
        kick_members:               メンバーをキックできるかどうか
        ban_members:                メンバーをBANできるかどうか
        manage_channels:            チャンネルを管理できるかどうか
        manage_guild:               サーバーを管理できるかどうか
        add_reactions:              メッセージにリアクションを追加できるかどうか
        view_audit_log:             サーバーの監査ログを表示できるかどうか
        priority_speaker:           優先スピーカーになれるかどうか
        stream:                     配信できるかどうか
        view_channel:               チャンネルを表示できるかどうか
        send_messages:              メッセージを送信できるかどうか
        send_tts_messages:          TTSメッセージを送信できるかどうか
        manage_messages:            メッセージを管理できるかどうか
        embed_links:                埋め込みリンクを送信できるかどうか
        attach_files:               ファイルを添付できるかどうか
        read_message_history:       メッセージ履歴を表示できるかどうか
        mention_everyone:           @everyoneや@hereを使用できるかどうか
        use_external_emojis:        外部の絵文字を使用できるかどうか
        view_guild_insights:        サーバーのインサイトを表示できるかどうか
        connect:                    ボイスチャンネルに接続できるかどうか
        speak:                      ボイスチャンネルで発言できるかどうか
        mute_members:               メンバーをミュートできるかどうか
        deafen_members:             メンバーをデフェンできるかどうか
        move_members:               メンバーを移動できるかどうか
        use_vad:                    音声検出を使用できるかどうか
        change_nickname:            ニックネームを変更できるかどうか
        manage_nicknames:           ニックネームを管理できるかどうか
        manage_roles:               ロールを管理できるかどうか
        manage_webhooks:            Webhookを管理できるかどうか
        manage_emojis_and_stickers: 絵文字とステッカーを管理できるかどうか
        use_application_commands:   アプリケーションコマンドを使用できるかどうか
        """
        self.administrator = False
        self.create_instant_invite = False
        self.kick_members = False
        self.ban_members = False
        self.manage_channels = False
        self.manage_guild = False
        self.add_reactions = False
        self.view_audit_log = False
        self.priority_speaker = False
        self.stream = False
        self.view_channel = False
        self.send_messages = False
        self.send_tts_messages = False
        self.manage_messages = False
        self.embed_links = False
        self.attach_files = False
        self.read_message_history = False
        self.mention_everyone = False
        self.use_external_emojis = False
        self.view_guild_insights = False
        self.connect = False
        self.speak = False
        self.mute_members = False
        self.deafen_members = False
        self.move_members = False
        self.use_vad = False
        self.change_nickname = False
        self.manage_nicknames = False
        self.manage_roles = False
        self.manage_webhooks = False
        self.manage_emojis_and_stickers = False
        self.use_application_commands = False
        self.request_to_speak = False
        self.manage_threads = False
        self.use_public_threads = False
        self.use_private_threads = False
        self.use_external_stickers = False

    def __or__(self, other: 'Permission') -> 'Permission':
        """
        2つのPermissionオブジェクトを論理和演算して、新しいPermissionオブジェクトを返すメソッド
        """
        result = Permission()  # 新しいPermissionオブジェクトを生成する
        result.administrator = self.administrator or other.administrator
        result.create_instant_invite = self.create_instant_invite or other.create_instant_invite
        result.kick_members = self.kick_members or other.kick_members
        result.ban_members = self.ban_members or other.ban_members
        result.manage_channels = self.manage_channels or other.manage_channels
        result.manage_guild = self.manage_guild or other.manage_guild
        result.add_reactions = self.add_reactions or other.add_reactions
        result.view_audit_log = self.view_audit_log or other.view_audit_log
        result.priority_speaker = self.priority_speaker or other.priority_speaker
        result.stream = self.stream or other.stream
        result.view_channel = self.view_channel or other.view_channel
        result.send_messages = self.send_messages or other.send_messages
        result.send_tts_messages = self.send_tts_messages or other.send_tts_messages
        result.manage_messages = self.manage_messages or other.manage_messages
        result.embed_links = self.embed_links or other.embed_links
        result.attach_files = self.attach_files or other.attach_files
        result.read_message_history = self.read_message_history or other.read_message_history
        result.mention_everyone = self.mention_everyone or other.mention_everyone
        result.use_external_emojis = self.use_external_emojis or other.use_external_emojis
        result.view_guild_insights = self.view_guild_insights or other.view_guild_insights
        result.connect = self.connect or other.connect
        result.speak = self.speak or other.speak
        result.mute_members = self.mute_members or other.mute_members
        result.deafen_members = self.deafen_members or other.deafen_members
        result.move_members = self.move_members or other.move_members
        result.use_vad = self.use_vad or other.use_vad
        result.change_nickname = self.change_nickname or other.change_nickname
        result.manage_nicknames = self.manage_nicknames or other.manage_nicknames
        result.manage_roles = self.manage_roles or other.manage_roles
        result.manage_webhooks = self.manage_webhooks or other.manage_webhooks
        result.manage_emojis_and_stickers = self.manage_emojis_and_stickers or other.manage_emojis_and_stickers
        result.use_application_commands = self.use_application_commands or other.use_application_commands
        result.request_to_speak = self.request_to_speak or other.request_to_speak
        result.manage_threads = self.manage_threads or other.manage_threads
        result.use_public_threads = self.use_public_threads or other.use_public_threads
        result.use_private_threads = self.use_private_threads or other.use_private_threads
        result.use_external_stickers = self.use_external_stickers or other.use_external_stickers

        return result

    def __and__(self, other: 'Permission') -> 'Permission':
        """
        2つのPermissionオブジェクトを論理積演算して、新しいPermissionオブジェクトを返すメソッド
        """
        result = Permission()  # 新しいPermissionオブジェクトを生成する
        result.administrator = self.administrator and other.administrator
        result.create_instant_invite = self.create_instant_invite and other.create_instant_invite
        result.kick_members = self.kick_members and other.kick_members
        result.ban_members = self.ban_members and other.ban_members
        result.manage_channels = self.manage_channels and other.manage_channels
        result.manage_guild = self.manage_guild and other.manage_guild
        result.add_reactions = self.add_reactions and other.add_reactions
        result.view_audit_log = self.view_audit_log and other.view_audit_log
        result.priority_speaker = self.priority_speaker and other.priority_speaker
        result.stream = self.stream and other.stream
        result.view_channel = self.view_channel and other.view_channel
        result.send_messages = self.send_messages and other.send_messages
        result.send_tts_messages = self.send_tts_messages and other.send_tts_messages
        result.manage_messages = self.manage_messages and other.manage_messages
        result.embed_links = self.embed_links and other.embed_links
        result.attach_files = self.attach_files and other.attach_files
        result.read_message_history = self.read_message_history and other.read_message_history
        result.mention_everyone = self.mention_everyone and other.mention_everyone
        result.use_external_emojis = self.use_external_emojis and other.use_external_emojis
        result.view_guild_insights = self.view_guild_insights and other.view_guild_insights
        result.connect = self.connect and other.connect
        result.speak = self.speak and other.speak
        result.mute_members = self.mute_members and other.mute_members
        result.deafen_members = self.deafen_members and other.deafen_members
        result.move_members = self.move_members and other.move_members
        result.use_vad = self.use_vad and other.use_vad
        result.change_nickname = self.change_nickname and other.change_nickname
        result.manage_nicknames = self.manage_nicknames and other.manage_nicknames
        result.manage_roles = self.manage_roles and other.manage_roles
        result.manage_webhooks = self.manage_webhooks and other.manage_webhooks
        result.manage_emojis_and_stickers = self.manage_emojis_and_stickers and other.manage_emojis_and_stickers
        result.use_application_commands = self.use_application_commands and other.use_application_commands
        result.request_to_speak = self.request_to_speak and other.request_to_speak
        result.manage_threads = self.manage_threads and other.manage_threads
        result.use_public_threads = self.use_public_threads and other.use_public_threads
        result.use_private_threads = self.use_private_threads and other.use_private_threads
        result.use_external_stickers = self.use_external_stickers and other.use_external_stickers

        return result


    async def get_permissions(self,permissions:int) -> None:
        """
        パーミッションを判別し、boolで返す
        param:
        permissions:int
            権限を表すコード
        """
        self.administrator = permissions & (1 << 3) == (1 << 3)
        self.create_instant_invite = permissions & (1 << 0) == (1 << 0)
        self.kick_members = permissions & (1 << 1) == (1 << 1)
        self.ban_members = permissions & (1 << 2) == (1 << 2)
        self.manage_channels = permissions & (1 << 4) == (1 << 4)
        self.manage_guild = permissions & (1 << 5) == (1 << 5)
        self.add_reactions = permissions & (1 << 6) == (1 << 6)
        self.view_audit_log = permissions & (1 << 7) == (1 << 7)
        self.priority_speaker = permissions & (1 << 8) == (1 << 8)
        self.stream = permissions & (1 << 9) == (1 << 9)
        self.view_channel = permissions & (1 << 10) == (1 << 10)
        self.send_messages = permissions & (1 << 11) == (1 << 11)
        self.send_tts_messages = permissions & (1 << 12) == (1 << 12)
        self.manage_messages = permissions & (1 << 13) == (1 << 13)
        self.embed_links = permissions & (1 << 14) == (1 << 14)
        self.attach_files = permissions & (1 << 15) == (1 << 15)
        self.read_message_history = permissions & (1 << 16) == (1 << 16)
        self.mention_everyone = permissions & (1 << 17) == (1 << 17)
        self.use_external_emojis = permissions & (1 << 18) == (1 << 18)
        self.view_guild_insights = permissions & (1 << 19) == (1 << 19)
        self.connect = permissions & (1 << 20) == (1 << 20)
        self.speak = permissions & (1 << 21) == (1 << 21)
        self.mute_members = permissions & (1 << 22) == (1 << 22)
        self.deafen_members = permissions & (1 << 23) == (1 << 23)
        self.move_members = permissions & (1 << 24) == (1 << 24)
        self.use_vad = permissions & (1 << 25) == (1 << 25)
        self.change_nickname = permissions & (1 << 26) == (1 << 26)
        self.manage_nicknames = permissions & (1 << 27) == (1 << 27)
        self.manage_roles = permissions & (1 << 28) == (1 << 28)
        self.manage_webhooks = permissions & (1 << 29) == (1 << 29)
        self.manage_emojis_and_stickers = permissions & (1 << 30) == (1 << 30)
        self.use_application_commands = permissions & (1 << 31) == (1 << 31)
        self.request_to_speak = permissions & (1 << 32) == (1 << 32)
        self.manage_threads = permissions & (1 << 34) == (1 << 34)
        self.use_public_threads = permissions & (1 << 35) == (1 << 35)
        self.use_private_threads = permissions & (1 << 36) == (1 << 36)
        self.manage_emojis_and_stickers = permissions & (1 << 42) == (1 << 42)
        self.use_external_stickers = permissions & (1 << 43) == (1 << 43)

    async def get_permission_code(self) -> int:
        permission_code = 0
        if self.administrator:
            permission_code += 8
        if self.create_instant_invite:
            permission_code += 1
        if self.kick_members:
            permission_code += 2
        if self.ban_members:
            permission_code += 4
        if self.manage_channels:
            permission_code += 16
        if self.manage_guild:
            permission_code += 32
        if self.add_reactions:
            permission_code += 64
        if self.view_audit_log:
            permission_code += 128
        if self.priority_speaker:
            permission_code += 256
        if self.stream:
            permission_code += 512
        if self.view_channel:
            permission_code += 1024
        if self.send_messages:
            permission_code += 2048
        if self.send_tts_messages:
            permission_code += 4096
        if self.manage_messages:
            permission_code += 8192
        if self.embed_links:
            permission_code += 16384
        if self.attach_files:
            permission_code += 32768
        if self.read_message_history:
            permission_code += 65536
        if self.mention_everyone:
            permission_code += 131072
        if self.use_external_emojis:
            permission_code += 262144
        if self.view_guild_insights:
            permission_code += 524288
        if self.connect:
            permission_code += 1048576
        if self.speak:
            permission_code += 2097152
        if self.mute_members:
            permission_code += 4194304
        if self.deafen_members:
            permission_code += 8388608
        if self.move_members:
            permission_code += 16777216
        if self.use_vad:
            permission_code += 33554432
        if self.change_nickname:
            permission_code += 67108864
        if self.manage_nicknames:
            permission_code += 134217728
        if self.manage_roles:
            permission_code += 268435456
        if self.manage_webhooks:
            permission_code += 536870912
        if self.manage_emojis_and_stickers:
            permission_code += 1073741824
        if self.use_application_commands:
            permission_code += 2147483648
        if self.request_to_speak:
            permission_code += 4294967296
        if self.manage_threads:
            permission_code += 8589934592
        if self.use_public_threads:
            permission_code += 34359738368
        if self.use_private_threads:
            permission_code += 68719476736
        if self.use_external_stickers:
            permission_code += 137438953472

        return permission_code



if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    p1 = Permission()
    p2 = Permission()
    loop.run_until_complete(
        p1.get_permissions(8)
    )
    loop.run_until_complete(
        p2.get_permissions(535059495090)
    )

    p3:Permission = p1 | p2

    print(p3.change_nickname)
    print(vars(p3))


