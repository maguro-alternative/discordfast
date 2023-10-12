from discord import Guild

from model_types.discord_type.guild_permission import Permission

async def return_permission(
    user_id:int,
    guild:Guild
) -> Permission:
    """
    指定されたユーザの権限を返す(ロールの権限も含む)

    guild_id        :int
        サーバのid
    user_id         :int
        ユーザのid
    access_token    :str
        ユーザのアクセストークン
    """
    user_permission = Permission()
    role_permission = Permission()
    permission_code = 0
    user = [
        member
        for member in guild.members
        if member.id == user_id
    ][0]

    # 権限コードをor計算で足し合わせる
    for role in user.roles:
        permission_code |= role.permissions.value

    await user_permission.get_permissions(permissions=user.guild_permissions.value)
    await role_permission.get_permissions(permissions=permission_code)

    return user_permission | role_permission