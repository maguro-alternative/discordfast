import json
import http.client  # httplibはPython3はhttp.clientへ移行
import httplib2
import os
import random
import sys
import time

from dotenv import load_dotenv
load_dotenv()

# YouTubeの認証情報をjson形式で作成
cli={
    "installed":
        {
            "client_id":os.environ["client_id"],
            "project_id":os.environ["project_id"],
            "auth_uri":"https://accounts.google.com/o/oauth2/auth",
            "token_uri":"https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
			"client_secret":os.environ["client_secret"],
			"redirect_uris":["http://localhost"]
		}
	}
with open(os.environ["CLIENT_SECRET_NAME"]+".json","w") as f:
    json.dump(cli,f, ensure_ascii=False, indent=4)

oau={
    "access_token":os.environ["access_token"],
    "client_id":os.environ["client_id"],
    "client_secret":os.environ["client_secret"],
    "refresh_token":os.environ["refresh_token"],
    "token_expiry": os.environ["token_expiry"], 
    "token_uri": "https://oauth2.googleapis.com/token",
    "user_agent": None,
    "revoke_uri": "https://oauth2.googleapis.com/revoke", 
    "id_token": None, 
    "id_token_jwt": None, 
    "token_response": {
        "access_token":os.environ["access_token"],
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

with open("upload_video.py-oauth2.json","w") as f:
    json.dump(oau,f, ensure_ascii=False, indent=4)

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error,
                        IOError,
                        http.client.NotConnected,
                        http.client.IncompleteRead,
                        http.client.ImproperConnectionState,
                        http.client.CannotSendRequest,
                        http.client.CannotSendHeader,
                        http.client.ResponseNotReady,
                        http.client.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# clientのjsonファイルのパス
CLIENT_SECRETS_FILE = os.environ["CLIENT_SECRET_NAME"]+".json"
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# abspath 現在の絶対パスを返す
# join 現在のパスを基準に他のファイルを読み込み
# dirname 現在のパスからupload_video.pyを除いたパスを表示

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

#  python upload_video.py --file="./movies/sino.mp4" --title="Sample Movie" --description="This is a sample movie." --category="22" --privacyStatus="unlisted"

def get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME,
                 YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            #print("Uploading file...")  # print文
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    #print("Video id '%s' was successfully uploaded." % response['id'])
                    # アップロードに成功した場合、idのみを表示する
                    # subprocess.runで出力結果からURLを生成するので、他のprintは出力しないこと！！
                    print(response['id'])
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % \
                        (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e
        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
              exit("No longer attempting to retry.")
            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)


if __name__ == '__main__':
#def main():
    argparser.add_argument("--file", help="Video file to upload",default=".\movies\a.mp4")
    argparser.add_argument("--title", help="Video title", default="Test Title")
    argparser.add_argument("--description",
                           help="Video description",
                           default="Test Description")
    argparser.add_argument("--category", default="22",
                           help="Numeric video category. " +
                                "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated",
                           default="")
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
                           default=VALID_PRIVACY_STATUSES[2],
                           help="Video privacy status.")
    args = argparser.parse_args()

    if not os.path.exists(args.file):
        exit("Please specify a valid file using the --file= parameter.")

    youtube = get_authenticated_service(args)
    try:
        initialize_upload(youtube, args)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
