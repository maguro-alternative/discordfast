let array = {}

const selectAdminAddEvent = (len,se,selectName) => {
    /*
    len:int
    既に設定されているメンバー、ロールの数

    se:HTMLinner
    select要素
    
    selectName:str
    選択された場合「名前：x」の形式で表示するdiv要素のid名
    */
    // idから要素を取得
    let selectId = document.getElementById(se.id);

    // チャンネルidのみを引き出す
    //const divId = se.id.substring(se.id.indexOf("_") + 1) 

    // すでにデータベース側にロールが設定された場合()
    if (len > 0){
        // チャンネルidをキーとした連想配列を作成
        array[se.id] = []
        for (let i = 0; i < len; i++){
            // ロールの数だけ代入
            array[se.id].push(i)
        }
    }

    function addSelectEvent(e) {
        const selectedItems = document.getElementById(selectName);

        // 二重に登録されないように削除
        selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

        const selectedOption = e.target.selectedOptions[0];
    
        const outerTextIndex = selectedItems.outerText.indexOf(selectedOption.textContent);
        
        // 既に登録されている場合
        if (outerTextIndex !== -1){
            console.log("return")
            return
        }
    
        // 登録されているロールの合計
        const xSum = selectedItems.outerText.split("x").length
    
        // 名前
        const item = document.createElement("div");
        item.className = "selected-item";
        item.textContent = selectedOption.textContent;
        
        // xボタン
        const removeBtn = document.createElement("span");
        removeBtn.className = "remove-item";
        removeBtn.textContent = "x";
    
        //input
        const hiddenItem = document.createElement("input");
        hiddenItem.className = "hidden-item";
        hiddenItem.type = "hidden";

        console.log(array)
        
        // 登録しようとしているチャンネルがある場合
        if (array[se.id]){

            console.log(se.id+" is true")
            // 一番最後の要素がある場合(前の要素が削除されている)
            if (array[se.id].includes(xSum)){

                // 削除された要素の中で一番小さい値を取得(nullが格納されている)
                let arrayNull = array[se.id].indexOf(null)
                console.log("uwagaki="+arrayNull)
                // 削除された要素に代入
                if (arrayNull > -1){
                    //
                    hiddenItem.name = selectedItems.id + "_" +(arrayNull + 1);
                    array[se.id][arrayNull] = (arrayNull + 1)
                }
            // 一番最後に代入
            }else{
                console.log("push="+xSum)
                array[se.id].push(xSum)
                hiddenItem.name = selectedItems.id + "_" + xSum;
            }
        // チャンネルの中身が空
        }else{
            console.log(se.id+" is false")
            array[se.id] = []
            array[se.id].push(xSum)
            hiddenItem.name = selectedItems.id + "_" + xSum;
        }
        hiddenItem.value = selectedOption.value;
        
        // xボタンをクリックしたら削除するように仕込む
        removeBtn.addEventListener("click", function () {
            // 削除する要素の番号
            let roleObjName = hiddenItem.name.substring(
                hiddenItem.name.lastIndexOf("_") + 1
            );
            
            // 1から始まるため-1にnull
            array[se.id][roleObjName - 1] = null
            item.remove();
            hiddenItem.remove();
            selectedOption.selected = false;
        });
        
        item.appendChild(removeBtn);
        selectedItems.appendChild(item);
        selectedItems.appendChild(hiddenItem)
        /*
        <div class="selected-item">
            @everyone
        <span class="remove-item">x</span></div>
        <input class="hidden-item" type="hidden" name="role_{{server_id}}_1" value="{{server_id}}">
        */

    }

    selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

    selectId.addEventListener("change", addSelectEvent);
}