from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any

from model_types.discord_type.discord_user_session import DiscordOAuthData,DiscordUser
from model_types.line_type.line_oauth import LineIdTokenResponse,LineOAuthData

class FastAPISession(BaseModel):
    discord_oauth_data  :Optional[DiscordOAuthData]
    discord_user        :Optional[DiscordUser]
    line_oauth_data     :Optional[LineOAuthData]
    line_user           :Optional[LineIdTokenResponse]