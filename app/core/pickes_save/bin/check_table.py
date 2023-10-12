from typing import List,Dict,Tuple
import re

async def check_table_type(
    columns:Dict,
    table_columns:Dict,
    new_columns:Dict,
    table_fetch:List[Dict]
) -> Tuple[bool,List[Dict]]:
    """
    テーブルのカラムに変更がないか確認する

    param:
    columns:Dict
        ローカル側のカラムの型

    table_columns:Dict
        データベース側のカラムの型

    new_columns:Dict
        ローカル側のカラムの初期値

    table_fetch:List[Dict]
        データベース側の現時点でのデータ

    return:
    Tuple[bool,List[Dict]]
        変更があった場合True
        変更があった場合、更新をしたあとの列

    """
    set_columns:Dict = {}

    # 新しく行が追加された場合
    create_items = [
        {key:value}
        for key,value in new_columns.items()
        if key not in table_columns.keys()
    ]

    # 行が削除された場合
    delete_items = [
        {key:value}
        for key,value in table_columns.items()
        if key not in new_columns.keys()
    ]

    for column_name,data_type in columns.items():
        table_data_type:str = table_columns.get(column_name)
        # (数字)が含まれていた場合、取り除く
        data_type:str = re.sub(r'\(\d+\)','',data_type)

        # データベース側になかった場合
        # 主キーで、変更があった場合
        if (table_data_type == None or
            table_data_type not in data_type.lower() and (
            'PRIMARY KEY' in data_type or
            'primary key' in data_type
            )):
            # listの場合tupleに変換(setがlist in listを扱えないため)
            if isinstance(new_columns[column_name],list):
                new_columns[column_name] = tuple(new_columns[column_name])
            set_columns.update(
                {
                    column_name:new_columns.get(column_name)
                }
            )
        # 完全一致(大文字小文字区別せず)あった場合
        # 主キーで、変更がない場合
        elif (table_data_type == data_type.lower() or
            (table_data_type in data_type.lower() and (
            'PRIMARY KEY' in data_type or
            'primary key' in data_type
            ))):
            set_columns.update(
                {
                    column_name:'Unchanged'
                }
            )

    # 要素の変更がある場合True
    if (len(list(set_columns.values())) == 1 and
        list(set_columns.values())[0] == "Unchanged"):
        unchanged = True
    else:
        unchanged = False

    # テーブルが存在する場合、要素を更新
    if len(table_fetch) > 0:
        if "does not exist" not in table_fetch[0]:
            for i,table in enumerate(table_fetch):
                table = dict(table)
                for table_key,table_value in table.items():
                    if set_columns.get(table_key) == "Unchanged":
                        table.update({table_key:table_value})

                # 追加する場合、デフォルトの値を代入
                for item in create_items:
                    for key,value in item.items():
                        table.update({key:value})

                # 削除された場合、削除
                for item in delete_items:
                    for key,value in item.items():
                        table.pop(key)

                table_fetch[i] = table

    return unchanged,table_fetch
