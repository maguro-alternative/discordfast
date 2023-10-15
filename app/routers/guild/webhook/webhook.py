from fastapi import APIRouter
from fastapi.responses import RedirectResponse,JSONResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from typing import List,Dict,Any,Union

from pkg.aio_req import aio_get_request
from pkg.oauth_check import discord_oauth_check,discord_get_profile
from pkg.permission import return_permission
from model_types.discord_type.guild_permission import Permission
from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser

from model_types.session_type import FastAPISession
from model_types.environ_conf import EnvConf

from model_types.table_type import WebhookSet,GuildSetPermission

from discord.channel import (
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
)
from discord import Guild
from discord.ext import commands
try:
    from core.start import DBot
    from core.db_create import DB
except ModuleNotFoundError:
    from app.core.start import DBot
    from app.core.db_create import DB

DISCORD_BASE_URL = EnvConf.DISCORD_BASE_URL
DISCORD_REDIRECT_URL = EnvConf.DISCORD_REDIRECT_URL

DISCORD_BOT_TOKEN = EnvConf.DISCORD_BOT_TOKEN

# デバッグモード
DEBUG_MODE = EnvConf.DEBUG_MODE

GuildChannel = Union[
    VoiceChannel,
    StageChannel,
    TextChannel,
    CategoryChannel
]

# new テンプレート関連の設定 (jinja2)
templates = Jinja2Templates(directory="templates")

class WebhookView(commands.Cog):
    def __init__(self, bot: DBot):
        self.bot = bot
        self.router = APIRouter()

        @self.router.get('/guild/{guild_id}/webhook')
        async def webhook(
            request:Request,
            guild_id:int
        ):
            # OAuth2トークンが有効かどうか判断
            if request.session.get('discord_oauth_data'):
                oauth_session = DiscordOAuthData(**request.session.get('discord_oauth_data'))
                user_session = DiscordUser(**request.session.get('discord_user'))
                # トークンの有効期限が切れていた場合、再ログインする
                if not await discord_oauth_check(access_token=oauth_session.access_token):
                    return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            else:
                return RedirectResponse(url=DISCORD_REDIRECT_URL,status_code=302)
            # Botが所属しているサーバを取得
            TABLE = f'webhook_set'

            # ログインユーザの情報を取得
            guild_user = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members/{user_session.id}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )
            role_list = [g for g in guild_user["roles"]]


            # サーバの権限を取得
            guild_user_permission = await return_permission(
                user_id=user_session.id,
                guild=[
                    guild
                    for guild in self.bot.guilds
                    if guild.id == guild_id
                ][0]
            )

            # パーミッションの番号を取得
            permission_code = await guild_user_permission.get_permission_code()

            if DB.conn == None:
                await DB.connect()

            guild_table:List[Dict[str,Any]] = await DB.select_rows(
                table_name='guild_set_permissions',
                columns=[],
                where_clause={
                    'guild_id':guild_id
                }
            )

            guild_permission_code = 8
            guild_permission_user = list()
            guild_permission_role = list()
            if len(guild_table) > 0:
                guild_permission_code = int(guild_table[0].get('webhook_permission'))
                guild_permission_user = [
                    user
                    for user in guild_table[0].get('webhook_user_id_permission')
                ]
                guild_permission_role = [
                    role
                    for role in guild_table[0].get('webhook_role_id_permission')
                ]

            and_code = guild_permission_code & permission_code
            admin_code = 8 & permission_code

            user_permission:str = 'normal'

            # 許可されている場合、管理者の場合
            if (and_code == permission_code or
                admin_code == 8 or
                user_session.id in guild_permission_user or
                len(set(guild_permission_role) & set(role_list)) > 0
                ):
                user_permission = 'admin'

            table_fetch:List[Dict[str,Any]] = await DB.select_rows(
                table_name=TABLE,
                columns=[],
                where_clause={
                    'guild_id':guild_id
                }
            )

            # webhook一覧を取得
            all_webhook = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/webhooks',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # サーバの情報を取得
            guild = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # サーバのチャンネル一覧を取得
            all_channel = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/channels',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            # 取得上限を定める
            limit = EnvConf.USER_LIMIT

            # サーバのメンバー一覧を取得
            guild_members = await aio_get_request(
                url = DISCORD_BASE_URL + f'/guilds/{guild_id}/members?limit={limit}',
                headers = {
                    'Authorization': f'Bot {DISCORD_BOT_TOKEN}'
                }
            )

            return templates.TemplateResponse(
                "guild/webhook/webhook.html",
                {
                    "request": request,
                    "guild": guild,
                    "guild_members":guild_members,
                    "guild_webhooks":all_webhook,
                    "table_webhooks":table_fetch,
                    "channels":all_channel,
                    "guild_id": guild_id,
                    "user_permission":user_permission,
                    "title": "webhookの送信設定/" + guild['name']
                }
            )

        @self.router.get('/guild/{guild_id}/webhook/view')
        async def webhook(
            guild_id:int,
            request:Request
        ) -> JSONResponse:
            session = FastAPISession(**request.session)
            if DB.conn == None:
                await DB.connect()
            # デバッグモード
            if DEBUG_MODE == False:
                # アクセストークンの復号化
                access_token = session.discord_oauth_data.access_token
                # Discordのユーザ情報を取得
                discord_user = await discord_get_profile(access_token=access_token)

                # トークンが無効
                if discord_user == None:
                    return JSONResponse(content={'message':'access token Unauthorized'})

            for guild in self.bot.guilds:
                if guild_id == guild.id:
                    # デバッグモード
                    if DEBUG_MODE:
                        chenge_permission = False
                    else:
                        # サーバの権限を取得
                        permission = await return_permission(
                            user_id=discord_user.id,
                            guild=guild
                        )

                        # 編集可能かどうか
                        chenge_permission = await chenge_permission_check(
                            user_id=discord_user.id,
                            permission=permission,
                            guild=guild
                        )

                    # Botが所属しているサーバを取得
                    TABLE = f'webhook_set'

                    db_webhooks:List[Dict] = await DB.select_rows(
                        table_name=TABLE,
                        columns=[],
                        where_clause={
                            'guild_id':guild_id
                        }
                    )

                    db_webhooks:List[WebhookSet] = [
                        WebhookSet(**w)
                        for w in db_webhooks
                    ]

                    db_webhooks:List[Dict] = [
                        vars(w)
                        for w in db_webhooks
                    ]

                    channels_json = dict()

                    all_webhook = await guild.webhooks()
                    webhooks = [
                        {
                            'id'            :str(w.id),
                            'name'          :w.name,
                            'channelId'     :str(w.channel_id),
                            'channelName'   :guild.get_channel(w.channel_id).name
                        }
                        for w in all_webhook
                    ]

                    # サーバー内のメンバー一覧
                    guild_users = [
                        {
                            'id'                :str(user.id),
                            'name'              :user.name,
                            'userDisplayName'   :user.display_name
                        }
                        for user in guild.members
                    ]

                    # サーバー内でのロール一覧
                    guild_roles = [
                        {
                            'id'    :str(user.id),
                            'name'  :user.name
                        }
                        for user in guild.roles
                    ]

                    channels_json.update({
                        'guildIcon'         :guild._icon,
                        'guildName'         :guild.name,
                        'webhooks'          :webhooks,
                        'guildUsers'        :guild_users,
                        'guildRoles'        :guild_roles,
                        'chengePermission'  :chenge_permission,
                        'webhookSet'        :db_webhooks
                    })

                    return JSONResponse(content=channels_json)

async def chenge_permission_check(
    user_id:int,
    permission:Permission,
    guild:Guild
) -> bool:
    """
    ログインユーザが編集可能かどうか識別

    Args:
        user_id (int):
            DiscordUserのid
        permission (Permission):
            ユーザの権限
        guild (Guild):
            サーバ情報

    Returns:
        bool: 編集可能かどうか
    """
    # パーミッションの番号を取得
    permission_code = await permission.get_permission_code()

    # アクセス権限の設定を取得
    guild_p:List[Dict] = await DB.select_rows(
        table_name='guild_set_permissions',
        columns=[],
        where_clause={
            'guild_id':guild.id
        }
    )
    guild_line_permission = GuildSetPermission(**guild_p[0])

    # 指定された権限を持っているか、管理者権限を持っているか
    and_code = guild_line_permission.webhook_permission & permission_code
    admin_code = 8 & permission_code

    # ロールid一覧を取得
    guild_user_data = guild.get_member(user_id)
    guild_user_roles = [
        role.id
        for role in guild_user_data.roles
    ]

    # 許可されている場合、管理者の場合
    if (and_code == permission_code or
        admin_code == 8 or
        user_id in guild_line_permission.webhook_user_id_permission or
        len(set(guild_line_permission.webhook_role_id_permission) & set(guild_user_roles)) > 0
        ):
        # 変更可能
        return True
    else:
        # 変更不可
        return False