let roleArray = {}
let memberArray = {}
let roleSelectArray = {}
let countArray = {}

// 使いません
const createInputTag = (
    guild_id,
    guildhooks,
    guildChannelIds,
    channel_ids,
    channel_names,
) => {
    //let getTag = document.getElementById(se.id);

    let webhookIds = []

    // select要素の作成(webhookのセレクト)
    let select_element = document.createElement('select');
    select_element.id = "webhookSelect_" + guild_id
    select_element.onchange = idChange(this,"webhookSelect_")
    //select_element.addEventListener('change',idChange)

    // option要素の作成(webhook一覧)
    for (let i = 0; i < guildhooks.length; i++){
        webhookIds.push(guildhooks[i])
        let option_element = document.createElement('option');
        for (let j = 0;j < channel_ids.length; j++){
            // 送信先チャンネルの要素が一致した場合
            if (channel_ids[j] == guildChannelIds[i]){
                // 値をwebhookのid、テキストをチャンネル名:webhook名にする
                option_element.value = guildhooks[i]
                //option_element.textContent = channel_names[j] + ":" + guildWebhookNames[i]
                // selectの子要素として格納
                select_element.appendChild(option_element)
                break
            }
        }
    }

    // input要素の追加(取得するサブスクの種類)
    let inputText = document.createElement('input')
    inputText.type = 'text'
    inputText.id = "subscType_" + guild_id
    inputText.onchange = idChange(this,"subscType_")
}

// フォームのコピーを作成する
const copyInputTag = (parentName) => {
    let elements = document.getElementById(parentName);

    // 一番最後の子要素のコピーを取得
    let copied = elements.lastElementChild.cloneNode(true);

    let copiedLen = elements.children.length
    let childRen = copied.children

    for (let i = 0;i < childRen.length;i++) {
        let baseIdName = childRen[i].id
        let idNum = 1

        // 末尾に数字がある場合
        if (/\d$/.test(childRen[i].id)){
            // 末尾の数字を削除
            idNum = /\d$/.exec(childRen[i].id)
            baseIdName = childRen[i].id.replace(/\d$/,"")
        }

        // ロール選択の要素の場合
        if (childRen[i].id.indexOf("role_select_") > -1) {
            // 子要素がなくなるまで削除(選択していたロールを削除)
            while (childRen[i].children.length) {
                childRen[i].children.item(0).remove()
            }
        }


        // キーワードOR検索の場合
        if (childRen[i].id.indexOf("searchOrWord_") > -1) {
            for (let j = 0;j < childRen[i].children.length; j++){

                let childBaseName = childRen[i].children[j].id
                let childIdNum = 1

                // 末尾に数字がある場合
                if (/\d$/.test(childRen[i].children[j].id)){
                    // 末尾の数字を削除
                    childIdNum = /\d$/.exec(childRen[i].children[j].id)
                    childBaseName = childRen[i].children[j].id.replace(/\d$/,"")
                }

                if (childRen[i].children[j].id.indexOf("searchOrAdd_") > -1){
                    // idの末尾に数を追加
                    childRen[i].children[j].id = childBaseName + copiedLen
                }
                if (childRen[i].children[j].className.indexOf("searchOrText") > -1){
                    childRen[i].children[j].remove()
                    j--
                }
                console.log(childRen[i].children[j])
            }
        }


        // キーワードAND検索の場合
        if (childRen[i].id.indexOf("searchAndWord_") > -1) {
            for (let j = 0;j < childRen[i].children.length; j++){

                let childBaseName = childRen[i].children[j].id
                let childIdNum = 1

                // 末尾に数字がある場合
                if (/\d$/.test(childRen[i].children[j].id)){
                    // 末尾の数字を削除
                    childIdNum = /\d$/.exec(childRen[i].children[j].id)
                    childBaseName = childRen[i].children[j].id.replace(/\d$/,"")
                }

                if (childRen[i].children[j].id.indexOf("searchAndAdd_") > -1){
                    // idの末尾に数を追加
                    childRen[i].children[j].id = childBaseName + copiedLen
                }
                if (childRen[i].children[j].className.indexOf("searchAndText") > -1){
                    childRen[i].children[j].remove()
                    j--
                }
                console.log(childRen[i].children[j])
            }
        }

        // NGワードOR検索の場合
        if (childRen[i].id.indexOf("ngOrWord_") > -1) {
            for (let j = 0;j < childRen[i].children.length; j++){

                let childBaseName = childRen[i].children[j].id
                let childIdNum = 1

                // 末尾に数字がある場合
                if (/\d$/.test(childRen[i].children[j].id)){
                    // 末尾の数字を削除
                    childIdNum = /\d$/.exec(childRen[i].children[j].id)
                    childBaseName = childRen[i].children[j].id.replace(/\d$/,"")
                }

                if (childRen[i].children[j].id.indexOf("ngOrAdd_") > -1){
                    // idの末尾に数を追加
                    childRen[i].children[j].id = childBaseName + copiedLen
                }
                if (childRen[i].children[j].className.indexOf("ngOrText") > -1){
                    childRen[i].children[j].remove()
                    j--
                }
                console.log(childRen[i].children[j])
            }
        }


        // NGワードAND検索の場合
        if (childRen[i].id.indexOf("ngAndWord_") > -1) {
            for (let j = 0;j < childRen[i].children.length; j++){

                let childBaseName = childRen[i].children[j].id
                let childIdNum = 1

                // 末尾に数字がある場合
                if (/\d$/.test(childRen[i].children[j].id)){
                    // 末尾の数字を削除
                    childIdNum = /\d$/.exec(childRen[i].children[j].id)
                    childBaseName = childRen[i].children[j].id.replace(/\d$/,"")
                }

                if (childRen[i].children[j].id.indexOf("ngAndAdd_") > -1){
                    // idの末尾に数を追加
                    childRen[i].children[j].id = childBaseName + copiedLen
                }
                if (childRen[i].children[j].className.indexOf("ngAndText") > -1){
                    childRen[i].children[j].remove()
                    j--
                }
                console.log(childRen[i].children[j])
            }
        }


        // メンションOR検索の場合
        if (childRen[i].id.indexOf("mentionOrWord_") > -1) {
            for (let j = 0;j < childRen[i].children.length; j++){

                let childBaseName = childRen[i].children[j].id
                let childIdNum = 1

                // 末尾に数字がある場合
                if (/\d$/.test(childRen[i].children[j].id)){
                    // 末尾の数字を削除
                    childIdNum = /\d$/.exec(childRen[i].children[j].id)
                    childBaseName = childRen[i].children[j].id.replace(/\d$/,"")
                }

                if (childRen[i].children[j].id.indexOf("mentionOrAdd_") > -1){
                    // idの末尾に数を追加
                    childRen[i].children[j].id = childBaseName + copiedLen
                }
                if (childRen[i].children[j].className.indexOf("mentionOrText") > -1){
                    childRen[i].children[j].remove()
                    j--
                }
                console.log(childRen[i].children[j])
            }
        }

        
        // メンションAND検索の場合
        if (childRen[i].id.indexOf("mentionAndWord_") > -1) {
            for (let j = 0;j < childRen[i].children.length; j++){

                let childBaseName = childRen[i].children[j].id
                let childIdNum = 1

                // 末尾に数字がある場合
                if (/\d$/.test(childRen[i].children[j].id)){
                    // 末尾の数字を削除
                    childIdNum = /\d$/.exec(childRen[i].children[j].id)
                    childBaseName = childRen[i].children[j].id.replace(/\d$/,"")
                }

                if (childRen[i].children[j].id.indexOf("mentionAndAdd_") > -1){
                    // idの末尾に数を追加
                    childRen[i].children[j].id = childBaseName + copiedLen
                }
                if (childRen[i].children[j].className.indexOf("mentionAndText") > -1){
                    childRen[i].children[j].remove()
                    j--
                }
                console.log(childRen[i].children[j])
            }
        }


        // コピー元のidを変更(末尾に子要素の数を付ける、コピー元に数はない)
        if (childRen[i].id.length > 0) {
            childRen[i].id = baseIdName + copiedLen
            childRen[i].name = baseIdName + copiedLen
        }
    }
    
    // 一番最後に追加
    elements.appendChild(copied);
}

// 使いません
function idChange(thisTag,parentName,idName){
    let getTag = document.getElementById(thisTag.id);
    let getParentTag = document.getElementById(parentName);
    
    // replaceですでにidが割り当てられているか判別
    let repTag = getTag.id.replace(idName,"")
    console.log(countArray)
    if (repTag.length === 0){
        countArray[0] = 1
        getTag.id = idName + countArray[0]
    }else{
        for (let i = 0; i < repTag; i++) {
            if (countArray[i] == null) {
                countArray[i] = i
                getTag.id = idName + countArray[i]
                break
            }
        }
    }
}


const selectWebhookRoleAddEvent = (roleLen,se) => {
    // idから要素を取得
    let selectId = document.getElementById(se.id);

    // チャンネルidのみを引き出す
    const divId = se.id.substring(se.id.indexOf("_") + 1) 

    // ロールが設定された場合
    if (roleLen > 0){
        // チャンネルidをキーとした連想配列を作成
        roleArray[se.id] = []
        for (let i = 0; i < roleLen; i++){
            // ロールの数だけ代入
            roleArray[se.id].push(i)
        }
    }

    function addSelectEvent(e) {
        const selectedItems = document.getElementById("role_select_" + divId);

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
        const roleSum = selectedItems.outerText.split("x").length
    
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
        
        // 登録しようとしているチャンネルがある場合
        if (roleArray[se.id]){
            console.log(se.id+" is true")
            // 一番最後の要素がある場合(前の要素が削除されている)
            if (roleArray[se.id].includes(roleSum)){
                // 削除された要素の中で一番小さい値を取得(nullが格納されている)
                let arrayNull = roleArray[se.id].indexOf(null)
                console.log("uwagaki="+arrayNull)
                // 削除された要素に代入
                if (arrayNull > -1){
                    hiddenItem.name = "role_" + selectedItems.id + "_" +(arrayNull + 1);
                    roleArray[se.id][arrayNull] = (arrayNull + 1)
                }
            // 一番最後に代入
            }else{
                console.log("push="+roleSum)
                roleArray[se.id].push(roleSum)
                hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
            }
        // チャンネルの中身が空
        }else{
            console.log(se.id+" is false")
            roleArray[se.id] = []
            roleArray[se.id].push(roleSum)
            hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
        }
        hiddenItem.value = selectedOption.value;
        
        // xボタンをクリックしたら削除するように仕込む
        removeBtn.addEventListener("click", function () {
            // 削除する要素の番号
            let roleObjName = hiddenItem.name.substring(
                hiddenItem.name.lastIndexOf("_") + 1
            );
            
            // 1から始まるため-1にnull
            roleArray[se.id][roleObjName - 1] = null
            item.remove();
            hiddenItem.remove();
            selectedOption.selected = false;
        });
        
        item.appendChild(removeBtn);
        selectedItems.appendChild(item);
        selectedItems.appendChild(hiddenItem)

    }

    selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

    selectId.addEventListener("change", addSelectEvent);
}




const selectWebhookMemberAddEvent = (memberLen,se) => {
    // idから要素を取得
    let selectId = document.getElementById(se.id);

    // チャンネルidのみを引き出す
    const divId = se.id.substring(se.id.indexOf("_") + 1) 

    // 設定されているロールがあった場合
    if (memberLen > 0){
        // チャンネルidをキーとした連想配列を作成
        memberArray[se.id] = []
        for (let i = 0; i < memberLen; i++){
            // ロールの数だけ代入
            memberArray[se.id].push(i)
        }
    }

    function addSelectEvent(e) {
        const selectedItems = document.getElementById("member_select_" + divId);

        // 二重に登録されないように削除
        selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

        const selectedOption = e.target.selectedOptions[0];
    
        const outerTextIndex = selectedItems.outerText.indexOf(selectedOption.textContent);
        
        if (outerTextIndex !== -1){
            console.log("return")
            return
        }
    
        const memberSum = selectedItems.outerText.split("x").length
    
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
        
        if (memberArray[se.id]){
            console.log(se.id+" is true")
            if (memberArray[se.id].includes(memberSum)){
                let arrayNull = memberArray[se.id].indexOf(null)
                console.log("uwagaki="+arrayNull)
                if (arrayNull > -1){
                    hiddenItem.name = "member_" + selectedItems.id + "_" +(arrayNull + 1);
                    memberArray[se.id][arrayNull] = (arrayNull + 1)
                }
            }else{
                console.log("push="+memberSum)
                memberArray[se.id].push(memberSum)
                hiddenItem.name = "member_" + selectedItems.id + "_" + memberSum;
            }
        // ロールの中身が空
        }else{
            console.log(se.id+" is false")
            memberArray[se.id] = []
            memberArray[se.id].push(memberSum)
            hiddenItem.name = "member_" + selectedItems.id + "_" + memberSum;
        }
        hiddenItem.value = selectedOption.value;
        
        // xボタンをクリックしたら削除するように仕込む
        removeBtn.addEventListener("click", function () {
            // 削除する要素の番号
            let memberObjName = hiddenItem.name.substring(hiddenItem.name.lastIndexOf("_") + 1);
            
            // 1から始まるため-1にnull
            memberArray[se.id][memberObjName - 1] = null
            item.remove();
            hiddenItem.remove();
            selectedOption.selected = false;
        });
        
        item.appendChild(removeBtn);
        selectedItems.appendChild(item);
        selectedItems.appendChild(hiddenItem)
    }

    selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

    selectId.addEventListener("change", addSelectEvent);
}



const changeWebhookRoleAddEvent = (roleLen,se) => {
    // idから要素を取得
    let selectId = document.getElementById(se.id);

    // チャンネルidのみを引き出す
    const divId = se.id.substring(se.id.indexOf("_") + 1) 

    // ロールが設定された場合
    if (roleLen > 0){
        // チャンネルidをキーとした連想配列を作成
        roleSelectArray[se.id] = []
        for (let i = 0; i < roleLen; i++){
            // ロールの数だけ代入
            roleSelectArray[se.id].push(i)
        }
    }

    function addSelectEvent(e) {
        const selectedItems = document.getElementById("role_change_" + divId);

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
        const roleSum = selectedItems.outerText.split("x").length
    
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
        
        // 登録しようとしているチャンネルがある場合
        if (roleSelectArray[se.id]){
            console.log(se.id+" is true")
            // 一番最後の要素がある場合(前の要素が削除されている)
            if (roleSelectArray[se.id].includes(roleSum)){
                // 削除された要素の中で一番小さい値を取得(nullが格納されている)
                let arrayNull = roleSelectArray[se.id].indexOf(null)
                console.log("uwagaki="+arrayNull)
                // 削除された要素に代入
                if (arrayNull > -1){
                    hiddenItem.name = "role_" + selectedItems.id + "_" +(arrayNull + 1);
                    roleSelectArray[se.id][arrayNull] = (arrayNull + 1)
                }
            // 一番最後に代入
            }else{
                console.log("push="+roleSum)
                roleSelectArray[se.id].push(roleSum)
                hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
            }
        // チャンネルの中身が空
        }else{
            console.log(se.id+" is false")
            roleSelectArray[se.id] = []
            roleSelectArray[se.id].push(roleSum)
            hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
        }
        hiddenItem.value = selectedOption.value;
        
        // xボタンをクリックしたら削除するように仕込む
        removeBtn.addEventListener("click", function () {
            // 削除する要素の番号
            let roleObjName = hiddenItem.name.substring(
                hiddenItem.name.lastIndexOf("_") + 1
            );
            
            // 1から始まるため-1にnull
            roleSelectArray[se.id][roleObjName - 1] = null
            item.remove();
            hiddenItem.remove();
            selectedOption.selected = false;
        });
        
        item.appendChild(removeBtn);
        selectedItems.appendChild(item);
        selectedItems.appendChild(hiddenItem)

    }

    selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

    selectId.addEventListener("change", addSelectEvent);
}



const changeWebhookMemberAddEvent = (memberLen,se) => {
    // idから要素を取得
    let selectId = document.getElementById(se.id);

    // チャンネルidのみを引き出す
    const divId = se.id.substring(se.id.indexOf("_") + 1) 

    // 設定されているロールがあった場合
    if (memberLen > 0){
        // チャンネルidをキーとした連想配列を作成
        memberArray[se.id] = []
        for (let i = 0; i < memberLen; i++){
            // ロールの数だけ代入
            memberArray[se.id].push(i)
        }
    }

    function addSelectEvent(e) {
        const selectedItems = document.getElementById("member_change_" + divId);

        // 二重に登録されないように削除
        selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

        const selectedOption = e.target.selectedOptions[0];
    
        const outerTextIndex = selectedItems.outerText.indexOf(selectedOption.textContent);
        
        if (outerTextIndex !== -1){
            console.log("return")
            return
        }
    
        const memberSum = selectedItems.outerText.split("x").length
    
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
        
        if (memberArray[se.id]){
            console.log(se.id+" is true")
            if (memberArray[se.id].includes(memberSum)){
                let arrayNull = memberArray[se.id].indexOf(null)
                console.log("uwagaki="+arrayNull)
                if (arrayNull > -1){
                    hiddenItem.name = "member_" + selectedItems.id + "_" +(arrayNull + 1);
                    memberArray[se.id][arrayNull] = (arrayNull + 1)
                }
            }else{
                console.log("push="+memberSum)
                memberArray[se.id].push(memberSum)
                hiddenItem.name = "member_" + selectedItems.id + "_" + memberSum;
            }
        // ロールの中身が空
        }else{
            console.log(se.id+" is false")
            memberArray[se.id] = []
            memberArray[se.id].push(memberSum)
            hiddenItem.name = "member_" + selectedItems.id + "_" + memberSum;
        }
        hiddenItem.value = selectedOption.value;
        
        // xボタンをクリックしたら削除するように仕込む
        removeBtn.addEventListener("click", function () {
            // 削除する要素の番号
            let memberObjName = hiddenItem.name.substring(hiddenItem.name.lastIndexOf("_") + 1);
            
            // 1から始まるため-1にnull
            memberArray[se.id][memberObjName - 1] = null
            item.remove();
            hiddenItem.remove();
            selectedOption.selected = false;
        });
        
        item.appendChild(removeBtn);
        selectedItems.appendChild(item);
        selectedItems.appendChild(hiddenItem)
    }

    selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

    selectId.addEventListener("change", addSelectEvent);
}





const addTextButton = (element,className) =>{
    const thisElement = document.getElementById(element.id)
    const thisParentElement = document.getElementById(thisElement.parentElement.id)
    //console.log()
    let formCount = 1,textCount = 1
    if (/\d$/.test(thisElement.parentElement.id)){
        formCount = /\d$/.exec(thisElement.parentElement.id)
    }
    // ortextのclassの数を取得
    textCount = document.getElementsByClassName(className + formCount).length + 1;
    
    const newForm = document.createElement('input');
    newForm.type = 'text';
    newForm.name = className + formCount + '_' + textCount;

    const newLabel = document.createElement('label');
    newLabel.textContent = 'キーワード(' + formCount + '-' + textCount + ')：';
    newLabel.className = className + formCount

    const newSpan = document.createElement('span');
    newSpan.classList.add('close-icon');
    newSpan.textContent = '✖';

    newLabel.appendChild(newForm);
    thisParentElement.appendChild(newLabel);
    thisParentElement.appendChild(newSpan);

    // 「✖」をクリックしたときの処理を追加
    newSpan.addEventListener('click', () => {
        // textを削除
        newLabel.remove();
        // 「✖」を削除
        newSpan.remove();
    });
}

// 既存要素の削除
const removeAdd = (removeItem) => {
    //.parentNodeで親要素の指定
    removeItem.parentNode.remove()
}

const removeTextBox = (removeText) => {
    // Labelのidの先頭には必ず、「key」がつく
    const textLabel = document.getElementById('key' + removeText.id)

    removeText.remove()
    textLabel.remove()
}







// 以降、使いません
const addSearchOrButton = (element) =>{
    const thisElement = document.getElementById(element.id)
    //console.log()
    let formCount = 1,textCount = 1
    if (/\d$/.test(thisElement.parentElement.id)){
        formCount = /\d$/.exec(thisElement.parentElement.id)
    }
    // ortextのclassの数を取得
    textCount = document.getElementsByClassName('orText' + formCount).length + 1;
    
    const newForm = document.createElement('input');
    newForm.type = 'text';

    const newLabel = document.createElement('label');
    newLabel.textContent = '連絡事項(' + formCount + '-' + textCount + ')：';
    newLabel.className = 'orText' + formCount

    newLabel.appendChild(newForm);
    document.getElementById(thisElement.parentElement.id).appendChild(newLabel);
}

const addSearchAndButton = (element) =>{
    const thisElement = document.getElementById(element.id)
    //console.log()
    let formCount = 1,textCount = 1
    if (/\d$/.test(thisElement.parentElement.id)){
        formCount = /\d$/.exec(thisElement.parentElement.id)
    }
    // ortextのclassの数を取得
    textCount = document.getElementsByClassName('orText' + formCount).length + 1;
    
    const newForm = document.createElement('input');
    newForm.type = 'text';

    const newLabel = document.createElement('label');
    newLabel.textContent = '連絡事項(' + formCount + '-' + textCount + ')：';
    newLabel.className = 'orText' + formCount

    newLabel.appendChild(newForm);
    document.getElementById(thisElement.parentElement.id).appendChild(newLabel);
}

const addMentionOrButton = (element) =>{
    const thisElement = document.getElementById(element.id)
    //console.log()
    let formCount = 1,textCount = 1
    if (/\d$/.test(thisElement.parentElement.id)){
        formCount = /\d$/.exec(thisElement.parentElement.id)
    }
    // ortextのclassの数を取得
    textCount = document.getElementsByClassName('orText' + formCount).length + 1;
    
    const newForm = document.createElement('input');
    newForm.type = 'text';

    const newLabel = document.createElement('label');
    newLabel.textContent = '連絡事項(' + formCount + '-' + textCount + ')：';
    newLabel.className = 'orText' + formCount

    newLabel.appendChild(newForm);
    document.getElementById(thisElement.parentElement.id).appendChild(newLabel);
}

const addMentionAndButton = (element) =>{
    const thisElement = document.getElementById(element.id)
    //console.log()
    let formCount = 1,textCount = 1
    if (/\d$/.test(thisElement.parentElement.id)){
        formCount = /\d$/.exec(thisElement.parentElement.id)
    }
    // ortextのclassの数を取得
    textCount = document.getElementsByClassName('orText' + formCount).length + 1;
    
    const newForm = document.createElement('input');
    newForm.type = 'text';

    const newLabel = document.createElement('label');
    newLabel.textContent = '連絡事項(' + formCount + '-' + textCount + ')：';
    newLabel.className = 'orText' + formCount

    newLabel.appendChild(newForm);
    document.getElementById(thisElement.parentElement.id).appendChild(newLabel);
}