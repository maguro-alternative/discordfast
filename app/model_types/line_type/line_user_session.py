from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any

class LineTokenVerify(BaseModel):
    """
    LINEのアクセストークンの有効性を示すクラス

    param:
    scope               :Optional[str]
        許可されている権限
    client_id           :Optional[str]
        クライアントid
    expires_in          :Optional[int]
        有効期限
    error               :Optional[str]
        エラー文
    error_description   :Optional[str]
        エラー内容
    """
    scope               :Optional[str]
    client_id           :Optional[str]
    expires_in          :Optional[int]
    error               :Optional[str]
    error_description   :Optional[str]