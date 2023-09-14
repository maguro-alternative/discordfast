from pydantic import BaseModel
from typing import List,Optional,Dict

class LineBotInfo(BaseModel):
    """
    ボットの情報
    https://developers.line.biz/ja/reference/messaging-api/#get-bot-info

    Args:
    basicId             :Optional[str]
        ボットのベーシックID
    chatMode            :Optional[str]
        チャットの設定
        chat:チャットがオン
        bot :チャットがオフ
    markAsReadMode      :Optional[str]
        メッセージの自動既読設定
        auto    :自動既読設定が有効
        manual  :自動既読設定が無効
    premiumId           :Optional[str]
        ボットのプレミアムID
        プレミアムIDが未設定の場合、この値は含まれない
    pictureUrl          :Optional[str]
        プロフィール画像のURL。「https://」から始まる画像UR
        ボットにプロフィール画像を設定していない場合は、レスポンスに含まれない
    displayName         :Optional[str]
        ボットの表示名
    userId              :Optional[str]
        ボットのユーザーID
    message             :Optional[str]
        エラー情報を含むメッセージ
    details             :Optional[List[Dict[str,str]]]
        エラー詳細の配列
        配列が空の場合は、レスポンスに含まれない
    """
    basicId             :Optional[str]
    chatMode            :Optional[str]
    markAsReadMode      :Optional[str]
    premiumId           :Optional[str]
    pictureUrl          :Optional[str]
    userId              :Optional[str]
    displayName         :Optional[str]
    message             :Optional[str]
    details             :Optional[List[Dict[str,str]]]

class LineBotFriend(BaseModel):
    """
    LINE Botの友達数
    https://developers.line.biz/ja/reference/messaging-api/#get-number-of-followers

    Args:
    status          :Optional[str]
        集計処理の状態
        ready:数値を取得
        unready:dateに指定した日付の友だち数の集計がまだ完了してない
        out_of_service:dateに指定した日付が、集計システムの稼働開始日（2016年11月1日）より前
    followers       :Optional[int]
        dateに指定した日付までに、アカウントが友だち追加された回数
    targetedReaches :Optional[int]
        dateに指定した日付時点の、性別や年齢、地域で絞り込んだターゲティングメッセージの配信先となりうる友だちの総数
    blocks          :Optional[int]
        dateに指定した日付時点で、アカウントをブロックしているユーザーの数
    message         :Optional[str]
        エラーメッセージ
    """
    status          :Optional[str]
    followers       :Optional[int]
    targetedReaches :Optional[int]
    blocks          :Optional[int]
    message         :Optional[str]

class LineGroupCount(BaseModel):
    """
    LINEグループにいる人数
    https://developers.line.biz/ja/reference/messaging-api/#get-quota

    Args:
    count   :Optional[int]
        人数
    message :Optional[str]
        エラーメッセージ
    """
    count   :Optional[int]
    message :Optional[str]

class LineBotQuota(BaseModel):
    """
    LINE Botの送信上限
    https://developers.line.biz/ja/reference/messaging-api/#get-quota

    Args:
    type    :Optional[str]
        上限目安が設定されているかどうかを示す値
        none:上限目安が未設定であることを示す
        limited:上限目安が設定されていることを示す
    value   :Optional[int]
        当月に送信できるメッセージ数の上限目安
    message :Optional[str]
        エラーメッセージ
    """
    type    :Optional[str]
    value   :Optional[int]
    message :Optional[str]

class LineBotConsumption(BaseModel):
    """
    LINE Botが送ったメッセージ数
    https://developers.line.biz/ja/reference/messaging-api/#get-consumption

    Args:
    totalUsage  :Optional[int]
        送ったメッセージの総数
    message     :Optional[str]
        エラーメッセージ
    """
    totalUsage  :Optional[int]
    message     :Optional[str]