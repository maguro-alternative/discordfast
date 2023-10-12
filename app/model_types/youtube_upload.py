import http.client  # httplibはPython3はhttp.clientへ移行
import httplib2
import os
import random
import io
import json

import aiofiles

import asyncio
from functools import partial

from googleapiclient.discovery import build,Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload,MediaIoBaseUpload,HttpRequest
from oauth2client.client import flow_from_clientsecrets,Credentials,OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run_flow

from model_types.environ_conf import EnvConf

# HTTPトランスポートライブラリに再試行を行わないよう明示的に伝える。
# リトライのロジックは本プログラムで処理するため。
httplib2.RETRIES = 1
# エラーが起きた際の最大再試行回数
MAX_RETRIES = 10
# これらの例外が発生した場合は常に再試行します。
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error,
                        IOError,
                        http.client.NotConnected,
                        http.client.IncompleteRead,
                        http.client.ImproperConnectionState,
                        http.client.CannotSendRequest,
                        http.client.CannotSendHeader,
                        http.client.ResponseNotReady,
                        http.client.BadStatusLine)

# これらのステータスコードエラーが発生した場合、 再試行を行います。
# コードが発生した場合は、常に再試行します。
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

"""
CLIENT_SECRETS_FILE変数は、client_idとclient_secretを含む、
このアプリケーションのOAuth 2.0情報を含むファイルの名前を指定します。
OAuth 2.0のクライアントIDとクライアントシークレットは、
以下のGoogle API Consoleから取得することができます。
https://console.cloud.google.com/

あなたのプロジェクトでYouTube Data APIが有効になっていることを確認してください.
YouTube Data APIにアクセスするためにOAuth2を利用する際の詳細な情報は、こちらを参照してください。
https://developers.google.com/youtube/v3/guides/authentication

client_secrets.jsonのファイルフォーマットに関する詳しい情報は, こちらを参照してください:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
"""
CLIENT_SECRETS_FILE = f"client_secret_{EnvConf.YOUTUBE_CLIENT_ID}.json"
OAUTH2_FILE = "upload_video.py-oauth2.json"

# この変数はCLIENT_SECRETS_FILEが見つからない場合に表示されるメッセージを定義します。
MISSING_CLIENT_SECRETS_MESSAGE = f"""
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

    {os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            CLIENT_SECRETS_FILE
        )
    )}

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
"""



"""
このOAuth 2.0のアクセススコープでは、アプリケーションが認証されたユーザーの YouTubeチャンネルにファイルをアップロードすることは許されますが、
それ以外のアクセスは許可されません。
認証されたユーザーの YouTube チャンネルにファイルをアップロードすることはできますが、
それ以外のアクセスはできません。
"""

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# publicで公開、privateで非公開、unlistedで限定公開
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

class YouTubeUpload():
    def __init__(
        self,
        file_path:str = None,
        title:str = None,
        description:str = None,
        tag:str = None,
        category_id:int = 22,
        privacy_status:str = "unlisted"
    ) -> None:
        """
        YouTubeに動画をアップロードするオブジェクト

        file_path:str
        動画ファイルのパス。

        title:str
        動画タイトル。

        description:str
        動画の説明欄。

        tag:str
        動画のタグ。カンマ区切りで区分けできる

        category_id:int
        カテゴリーのid。詳細は下記参照。
        https://gist.github.com/dgp/1b24bf2961521bd75d6c

        privacy_status:str
        動画の公開形式。
        publicで公開、privateで非公開、unlistedで限定公開
        """
        self.file_path = file_path
        self.title = title
        self.description = description
        self.tag = tag
        self.category_id = category_id
        self.privacy_status = privacy_status
        self.loop = asyncio.get_event_loop()


    async def create_client_secret(self) -> None:
        # YouTubeの認証情報をjson形式で作成
        cli = {
            "installed":
                {
                    "client_id":EnvConf.YOUTUBE_CLIENT_ID,
                    "project_id":EnvConf.YOUTUBE_PROJECT_ID,
                    "auth_uri":"https://accounts.google.com/o/oauth2/auth",
                    "token_uri":"https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret":EnvConf.YOUTUBE_CLIENT_SECRET,
                    "redirect_uris":["http://localhost"]
                }
        }
        async with aiofiles.open(CLIENT_SECRETS_FILE,"w") as f:
            json_data = json.dumps(cli)
            await f.write(json_data)
            await f.close()

    async def create_oauth(self) -> None:
        oau = {
            "access_token":EnvConf.YOUTUBE_ACCESS_TOKEN,
            "client_id":EnvConf.YOUTUBE_CLIENT_ID,
            "client_secret":EnvConf.YOUTUBE_CLIENT_SECRET,
            "refresh_token":EnvConf.YOUTUBE_REFRESH_TOKEN,
            "token_expiry": EnvConf.YOUTUBE_TOKEN_EXPIRY,
            "token_uri": "https://oauth2.googleapis.com/token",
            "user_agent": None,
            "revoke_uri": "https://oauth2.googleapis.com/revoke",
            "id_token": None,
            "id_token_jwt": None,
            "token_response": {
                "access_token":EnvConf.YOUTUBE_ACCESS_TOKEN,
                "expires_in": 3599,
                "scope": "https://www.googleapis.com/auth/youtube.upload",
                "token_type": "Bearer"
            },
            "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
            "token_info_uri": "https://oauth2.googleapis.com/tokeninfo",
            "invalid": False,
            "_class": "OAuth2Credentials",
            "_module": "oauth2client.client"
        }
        async with aiofiles.open(OAUTH2_FILE,"w") as f:
            json_data = json.dumps(oau)
            await f.write(json_data)
            await f.close()


    async def get_authenticated_service(self) -> Resource:
        """
        認証フロー?を作成しYouTubeAPIのリソースを作成

        return
        youtube:Resource
        動的生成されたYouTubeAPIのオブジェクト
        """

        if not bool(os.path.isfile(CLIENT_SECRETS_FILE)):
            await self.create_client_secret()

        if not bool(os.path.isfile(OAUTH2_FILE)):
            await self.create_oauth()

        flow:OAuth2WebServerFlow = flow_from_clientsecrets(
            filename=CLIENT_SECRETS_FILE,
            scope=YOUTUBE_UPLOAD_SCOPE,
            message=MISSING_CLIENT_SECRETS_MESSAGE
        )

        # 認証情報を取得
        storage = Storage(OAUTH2_FILE)
        credentials:Credentials = storage.get()

        # OAuthファイルが見つからない場合
        if credentials is None or credentials.invalid:
            credentials = run_flow(flow = flow, storage = storage)

        # 生成したYouTubeAPIのオブジェクトを返す
        return build(
            serviceName=YOUTUBE_API_SERVICE_NAME,
            version=YOUTUBE_API_VERSION,
            http=credentials.authorize(httplib2.Http())
        )

    async def byte_upload(
        self,
        video_bytes:io.BytesIO,
        youtube:Resource
    ) -> str:
        """
        動画のバイナリデータから直接YouTubeにアップロードする。

        param
        video_bytes:io.BytesIO
        動画のバイナリデータ

        youtube:Resource
        動的生成されたYouTubeAPIのオブジェクト

        return
        youtube_id:str
        アップロードした動画のid
        """
        # タグ(カンマ区切り)があった場合、格納
        tags:list = None
        if self.tag:
            tags = self.tag.split(",")

        # 動画バイナリからアップロード用のデータを生成
        media = MediaIoBaseUpload(
            fd=video_bytes,
            mimetype='video/*',
            chunksize=1024*1024,
            resumable=True
        )

        # videos.insertで動画をアップロード
        request:HttpRequest = await self.loop.run_in_executor(
            None,
            partial(
                youtube.videos().insert,
                part='snippet,status',
                body={
                    'snippet': {
                        'title': self.title,
                        'description': self.description,
                        'tags': tags,
                        'categoryId': self.category_id
                    },
                    'status': {
                        'privacyStatus': self.privacy_status
                    }
                },
                media_body=media
            )
        )

        # 動画のidを取得
        youtube_id = await self.resumable_upload(request)
        return youtube_id


    # 失敗したアップロードを再開するために指数関数的なバックオフ戦略を実装しています。
    async def resumable_upload(self,insert_request:HttpRequest) -> str:
        """
        正常なアップロードができるまでアップロードを繰り返します。

        param
        insert_request  :HttpRequest
        動画のアップロード情報を格納するオブジェクト

        return:
        youtube_id      :str
        """
        response:dict = None
        error:str = None
        retry:int = 0
        video_id:str = None
        print("アップロード中...")
        while response is None:
            try:
                status, response = await self.loop.run_in_executor(
                    None,
                    partial(
                        insert_request.next_chunk,
                    )
                )
                if response is not None:
                    if 'id' in response:
                        print(f"アップロードに成功しました。動画ID:{response['id']}")
                        video_id = response['id']
                    else:
                        exit(f"アップロードに失敗しました。レスポンス: {response}")
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"HTTPエラー {e.resp.status} が発生しました。:\n{e.content}"
                else:
                    raise
            except RETRIABLE_EXCEPTIONS as e:
                error = f"リトライ可能なエラーが発生しました。: {e}"
            if error is not None:
                print(error)
                retry += 1
                if retry > MAX_RETRIES:
                    exit("リトライ回数の上限に達しました。")
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(f"{sleep_seconds}秒後、再アップロードを試みます。")
                await asyncio.sleep(sleep_seconds)

        return video_id