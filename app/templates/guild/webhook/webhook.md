# webhook
データベース側へ登録する各項目  
_がついているものは末尾に数字がつく。  
1から始まるものは項目が複数あることを示す。
```
"webhookSelect_",
"subscType_",
"subscId_",             
"role_role_select_",
"member_member_select_",
"searchOrText",
"searchAndText",
"ngOrText",
"ngAndText",
"mentionOrText",
"mentionAndText",

"webhookChange_",
"subscTypeChange_",
"subscIdChange_",       
"role_role_change_",
"member_member_change_",
"changeSearchOrText",
"changeSearchAndText",
"changeNgOrText",
"changeNgAndText",
"changeMentionOrText",
"changeMentionAndText"
```
# 新規作成
## webhookSelect_ :int
使用するwebhookのid  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## subscType_ :str
送信するサービス元のサービス名(Twitter,niconico)  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## subscId_ :str
サービスでのid(Twitter:@以降の名前,niconico:ユーザ番号)  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## role_role_select_ :int
送信された場合に通知するロールのid  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## member_member_select_ :int
上記と同様にメッセージが送信された場合に通知するメンバーのid  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## searchOrText :str
テキストにこの項目に指定されたいずれかの文字が含まれていた場合に送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## searchAndText :str
テキストにこの項目に指定された文字すべてが含まれていた場合に送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## ngOrText :str
テキストにこの項目に指定されたいずれかの文字が含まれていた場合は送信しない。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## ngAndText :str
テキストにこの項目に指定された文字すべてが含まれていた場合は送信しない。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## mentionOrText :str
テキストにこの項目に指定されたいずれかの文字が含まれていた場合にメンションをつけて送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## mentionAndText :str
テキストにこの項目に指定された文字すべてが含まれていた場合にメンションをつけて送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

# 変更
## webhookChange_ :int
使用するwebhookのid  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## subscTypeChange_ :str
送信するサービス元のサービス名(Twitter,niconico)  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## subscIdChange_ :str
サービスでのid(Twitter:@以降の名前,niconico:ユーザ番号)  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## role_role_change_ :int
送信された場合に通知するロールのid  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## member_member_change_ :int
上記と同様にメッセージが送信された場合に通知するメンバーのid  
末尾には1が付き、複数の項目が送られて来ると2,3と続いてくる。

## changeSearchOrText :str
テキストにこの項目に指定されたいずれかの文字が含まれていた場合に送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## changeSearchAndText :str
テキストにこの項目に指定された文字すべてが含まれていた場合に送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## changeNgOrText :str
テキストにこの項目に指定されたいずれかの文字が含まれていた場合は送信しない。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## changeNgAndText :str
テキストにこの項目に指定された文字すべてが含まれていた場合は送信しない。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## changeMentionOrText :str
テキストにこの項目に指定されたいずれかの文字が含まれていた場合にメンションをつけて送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。

## changeMentionAndText :str
テキストにこの項目に指定された文字すべてが含まれていた場合にメンションをつけて送信する。  
niconico,YouTubeには非対応  
末尾には1が付き、更に_1とついてくる。  
_以降の数字はテキストの数を示している。  
複数の項目が送られて来ると両者ともに2,3と続いてくる。