import datetime
import requests
import calendar
import os
import math

def linereq(url,token,jsonkey):

    return (requests.request(
		"get",
		url=url,
		headers={
            'Authorization': 'Bearer ' + token
		}
	)).json()[jsonkey]

class DayGet:
    def __init__(self,name:str):
        self.token=os.environ.get(f'{name}_ACCESS_TOKEN')
        self.group_id=os.environ.get(f"{name}_GROUP_ID")    #グループIDなしの場合、None
		
    # 当月のメッセージ利用状況を取得
    def totalpush(self) -> int:
        return linereq(
            "https://api.line.me/v2/bot/message/quota/consumption",
            self.token,
            "totalUsage"
            )
    
    # 友達数、グループ人数をカウント
    def friend(self):
        # グループIDなしの場合、友達数をカウント
        if self.group_id == None:
            if datetime.datetime.now().strftime('%H') == '00':
                url="https://api.line.me/v2/bot/insight/followers?date="+(datetime.date.today()+datetime.timedelta(days=-1)).strftime('%Y%m%d')
            else:
                url="https://api.line.me/v2/bot/insight/followers?date="+datetime.date.today().strftime('%Y%m%d')
            return linereq(
                url,
                self.token,
                "followers"
            )
        else:
            return linereq(
				"https://api.line.me/v2/bot/group/"+self.group_id+"/members/count",
				self.token,
				"count"
			)
    # 当月に送信できるメッセージ数の上限目安を取得(基本1000)
    def pushlimit(self):
        return linereq(
            "https://api.line.me/v2/bot/message/quota",
            self.token,
            "value"
            )

    # 現在の時刻
    def today_time(self):
        return datetime.datetime.now()
    # 現在の日付
    def today(self):
        return datetime.datetime.now().day
    # 今月末の日
    def endmonth(self):
        return calendar.monthrange(datetime.datetime.now().year, datetime.datetime.now().month)[1]

class Limit(DayGet):
    def __init__(self,name:str):
        super().__init__(name)
    
    # 1000/30=33.3333
    def onedaypush(self) -> float:
        """
        onedaypush

        当月分のメッセージ上限を月末の日付で割った値
        
        戻り値例:float
        メッセージ上限=1000件
        月末の日付=30日

        1000/30=33.333...
        """
        return super().pushlimit()/super().endmonth()
    
    # 0/1 297/17=17.4705
    def todaypush(self) -> float:
        """
        todaypush

        当月分のプッシュ数を現在の日付で割った値
        また、この時点では送信前の値となる
        
        戻り値例:float
        メッセージ送信数=297件
        現在の日付=17日

        297/17=17.4705
        """
        return super().totalpush()/super().today()
    
    # (0+1)/1 (297+11)/17=18.117
    def afterpush(self) -> float:
        """
        afterpush

        当月分のプッシュ数に友達数(1回送信した)を足して、現在の日付で割った値
        送信後の値になる

        戻り値例:float
        メッセージ送信数=297件
        友達数=11人
        現在の日付=17日

        (297+11)/17=18.117
        """
        return (super().totalpush()+super().friend())/super().today()

    # 0+1 297+11=308
    def aftertotal(self) -> int:
        """
        aftertotal

        当月分のプッシュ数に友達数(1回送信した)を足した値
        送信後の値になる

        戻り値例:int
        メッセージ送信数=297件
        友達数=11人

        297+11=308
        """
        return super().totalpush()+super().friend()

class Push(Limit):
    def __init__(self,name:str):
        super().__init__(name)

    # 1-0 18.117-17.4705=0.6465
    def consumption(self) -> float:
        """
        consumption

        1回送信するたびに消費される上限数

        戻り値例:float
        メッセージ送信数=297件
        友達数=11人
        現在の日付=17日

        当月分のプッシュ数に友達数を足して、現在の日付で割った値=(297+11)/17=18.117
        当月分のプッシュ数を現在の日付で割った値=297/17=17.4705

        18.117-17.4705=0.6465
        """
        return super().afterpush()-super().todaypush()

class PushLimit(Push):
    def __init__(self,name:str):
        super().__init__(name)
	
    # (33.333-0)/1
    def daylimit(self) -> int:
        """
        daylimit

        消費される上限数から本日分の上限を計算(小数点以下切り上げ)

        戻り値例:int
        メッセージ送信数=297件
        友達数=11人
        現在の日付=17日
        月末の日付=30日

        当月分のメッセージ上限を月末の日付で割った値=1000/30=33.333
        当月分のプッシュ数に友達数を足して、現在の日付で割った値=(297+11)/17=18.117
        1回送信するたびに消費される上限数=18.117-17.4705=0.6465

        (33.333-18.117)/0.6465=23.53=24
        """
        return math.ceil((super().onedaypush()-super().afterpush())/super().consumption())

    # 33.333/1
    def templelimit(self) -> int:
        """
        templelimit

        1日当たりの上限を計算(小数点以下切り上げ)

        戻り値例:int
        友達数=11人
        月末の日付=30日

        当月分のメッセージ上限を月末の日付で割った値=1000/30=33.333

        33.333/11=3.0303=4
        """
        return math.ceil(super().onedaypush()/super().friend())

if __name__=="main":
    limit=PushLimit(name='')

    print(f"一か月分のプッシュ上限 {limit.pushlimit()}")
    print(f"今月分のプッシュ数 {limit.totalpush()}")
    print(f"1送信につき消費するプッシュ数（botの友達数) {limit.friend()}")
    print(f"本日分のプッシュ上限 {limit.onedaypush()}")
    print(f"本日のプッシュ数 {limit.todaypush()}")
    print(f"1送信につき消費するプッシュ数 {limit.consumption()}")
    print(f"残り送信上限 {limit.daylimit()}")