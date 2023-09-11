from pydantic import BaseModel
from typing import Optional

from model_types.discord_type.discord_user_session import DiscordOAuthData
from model_types.discord_type.discord_type import DiscordUser
from model_types.line_type.line_oauth import LineIdTokenResponse,LineOAuthData

class FastAPISession(BaseModel):
    discord_oauth_data  :Optional[DiscordOAuthData]
    discord_user        :Optional[DiscordUser]
    line_oauth_data     :Optional[LineOAuthData]
    line_user           :Optional[LineIdTokenResponse]