from pydantic import BaseModel,validator
from typing import List,Optional,Union,Any

class LineProfile(BaseModel):
    """
    LINEのユーザプロフィール

    param:
    displayName :Optional[str]
        ユーザ名
    userId      :Optional[str]
        ユーザid
    pictureUrl  :Optional[str]
        アイコンのURL
    message     :Optional[str]
        エラーメッセージ
    """
    displayName     :Optional[str]
    userId          :Optional[str]
    pictureUrl      :Optional[str]
    status_message  :Optional[str]
    message         :Optional[str]


class LineCallbackRequest(BaseModel):
    """
    /line-callback/で受け取るデータ

    param:
    guild_id    :int
        Discordサーバーのid
    code        :int
        認証に使用するコード
    nonce       :str
        認証時に使用するランダムデータ
    """
    guild_id    :int
    code        :int
    nonce       :str

class LineOAuthData(BaseModel):
    """
    LINEのOAuth2認証のデータ
    https://developers.line.biz/ja/reference/line-login/#issue-access-token

    param:
    access_token    :str
        ユーザのアクセストークン
    expires_in      :int
        アクセストークンの有効期限(秒)
    id_token        :str
        ユーザー情報を含むJSONウェブトークン（JWT）
    refresh_token   :str
        リフレッシュトークン
    scope           :str
        許可されている権限
    token_type      :str
        トークンのタイプ
        Bearer
    """
    access_token    :str
    expires_in      :int
    id_token        :str
    refresh_token   :str
    scope           :str
    token_type      :str

class LineIdTokenResponse(BaseModel):
    """
    Lineのidトークンのレスポンス

    param:
    iss         :str
        IDトークンの生成URL
    sub         :str
        IDトークンの対象ユーザーID
    aud         :str
        チャネルID
    exp         :int
        IDトークンの有効期限。UNIXタイム
    iat         :int
        IDトークンの生成時間。UNIXタイム
    auth_time   :Optional[int]
        ユーザー認証時間。UNIXタイム
        認可リクエストにmax_ageの値を指定しなかった場合は含まれない
    nonce       :Optional[str]
        認可URLに指定したnonceの値
        認可リクエストにnonceの値を指定しなかった場合は含まれない
    amr         :Optional[List[str]]
        ユーザーが使用した認証方法のリスト
        特定の条件下ではペイロードに含まれない

        以下のいずれかの値が含まれます。

        pwd             :メールアドレスとパスワードによるログイン
        lineautologin   :LINEによる自動ログイン（LINE SDKを使用した場合も含む）
        lineqr          :QRコードによるログイン
        linesso         :シングルサインオンによるログイン
    name        :Optional[str]
        ユーザーの表示名
        認可リクエストにprofileスコープを指定しなかった場合は含まれない
    picture     :Optional[str]
        ユーザープロフィールの画像URL
        認可リクエストにprofileスコープを指定しなかった場合は含まれない
    email       :Optional[str]
        ユーザーのメールアドレス
        認可リクエストにemailスコープを指定しなかった場合は含まれない
    """
    iss         :str
    sub         :str
    aud         :str
    exp         :int
    iat         :int
    auth_time   :Optional[int]
    nonce       :Optional[str]
    amr         :Optional[List[str]]
    name        :Optional[str]
    picture     :Optional[str]
    email       :Optional[str]

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