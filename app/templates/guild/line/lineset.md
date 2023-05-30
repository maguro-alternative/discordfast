# lineset
lineからdiscordへのメッセージ送信の設定項目

```bash
'line_notify_token',
'line_bot_token',
"line_bot_secret",
'line_group_id',
'default_channel_id',
'debug_mode'
```

## line_notify_token :str
LINE Notifyのトークン  
暗号化されbytesでsqlに格納される

## line_bot_token :str
LINE Botのトークン  
暗号化されbytesでsqlに格納される

## line_bot_secret :str
LINE Botのシークレットキー  
暗号化されbytesでsqlに格納される

## line_group_id :str
LINEグループのid  
暗号化されbytesでsqlに格納される

## default_channel_id :int
LINEからのメッセージをDiscordに送信する際のチャンネルid  
デフォルトではシステムチャンネルになる

## debug_mode :bool
LINEグループでメッセージを送信するとNotifyがLINEグループのidを返信するモード  
Trueにすると有効になる  
事前にline_notify_tokenとline_bot_tokenとline_bot_secretは入力しておくこと