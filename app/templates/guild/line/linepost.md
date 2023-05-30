# linepost
discordからlineへのメッセージ送信の設定項目

```bash
"line_ng_channel_{channel_id}",
"message_bot_{channel_id}",
"default_{channel_id}",
"recipient_add_{channel_id}",
"pins_add_{channel_id}",
"member_{channel_id}"
```

## line_ng_channel_{channel_id} :bool
このチャンネルのメッセージはlineに送信するかしないか  
Trueの場合、このチャンネルのメッセージはlineに送信されない

## message_bot_{channel_id} :bool
このチャンネルのBotのメッセージはlineに送信するかしないか  
Trueの場合、このチャンネルのBotのメッセージはlineに送信されない

## default_{channel_id} :bool
デフォルトのメッセージ
## recipient_add_{channel_id} :bool
返信のメッセージ
## pins_add_{channel_id} :bool
ピン止めのメッセージ

上記のものがFalseだった場合、lineに送信されない

## member_{channel_id}_{i} :int
送信NGのユーザid  
iはidの数を表し、startswithで数を数えている  
(順番が不定、欠けがあっても数えることが可能)  
設定されているユーザーのメッセージはlineに送信されない