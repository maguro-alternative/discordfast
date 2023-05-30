## admin
サーバー管理者がほかの機能を操作する権限を設定する項目

```bash
line_permission_code,
member_select_line_{i},
role_select_line_{i},

line_bot_permission_code,
member_select_line_bot_{i},
role_select_line_bot_{i},

vc_permission_code,
member_select_vc_{i},
role_select_vc_{i},

webhook_permission_code,
member_select_webhook_{i},
role_select_webhook_{i}
```
## _permission_code :int
該当項目の操作ができる権限を表す権限コード 
操作するにはコードが示す全ての権限を持っている必要がある(orではなくand)   
基本は8(admin)

## member_select_{}_{i} :int
該当項目の操作ができるユーザーのidを表す  

## role_select_{}_{i} :int
該当項目の操作ができるロールのidを表す  
