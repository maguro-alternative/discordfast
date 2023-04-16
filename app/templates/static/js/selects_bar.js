//const select = document.getElementById("mySelect");
//const selectedItems = document.querySelector(".selected-items");

let roleArray = {}
/*
select.addEventListener("change", function (e) {
    const selectedOption = e.target.selectedOptions[0];

    const outerTextIndex = selectedItems.outerText.indexOf(selectedOption.textContent);
    
    if (outerTextIndex !== -1){
        return
    }

    const roleSum = selectedItems.outerText.split("x").length

    // 
    let roleNum = document.querySelectorAll(".hidden-item")

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
    console.log(roleSum,roleArray.indexOf(null))
    if (roleArray.includes(roleSum)){
        let arrayNull = roleArray.indexOf(null)
        if (arrayNull > -1){
            hiddenItem.name = "role_" + selectedItems.id + "_" +(arrayNull + 1);
            roleArray[arrayNull] = (arrayNull + 1)
        }
    }else{
        roleArray.push(roleSum)
        hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
    }
    hiddenItem.value = selectedOption.value;

    console.log(roleArray)
    
    // xボタンをクリックしたら削除するように仕込む
    removeBtn.addEventListener("click", function () {
        // 削除する要素の番号
        let roleObjName = hiddenItem.name.substring(hiddenItem.name.lastIndexOf("_") + 1);
        
        roleArray[roleObjName - 1] = null
        item.remove();
        hiddenItem.remove();
        selectedOption.selected = false;
    });
    
    item.appendChild(removeBtn);
    selectedItems.appendChild(item);
    selectedItems.appendChild(hiddenItem)
});
*/

/*
const selectAddEvent = (se) => {
    let selectId = document.getElementById(se.id);
    const selectedItems = document.querySelector(".selected-items");
    console.log(selectId)
    console.log(se.id)
    selectId.addEventListener("change", function (e) {
        const selectedOption = e.target.selectedOptions[0];
    
        const outerTextIndex = selectedItems.outerText.indexOf(selectedOption.textContent);
        
        if (outerTextIndex !== -1){
            console.log("return")
            return
        }
    
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
        //console.log(roleSum,roleArray[se.id].indexOf(null))
        if (roleArray[se.id]){
            console.log(se.id+" is true")
            if (roleArray[se.id].includes(roleSum)){
                let arrayNull = roleArray[se.id].indexOf(null)
                console.log("uwagaki="+arrayNull)
                if (arrayNull > -1){
                    hiddenItem.name = "role_" + selectedItems.id + "_" +(arrayNull + 1);
                    roleArray[se.id][arrayNull] = (arrayNull + 1)
                }
            }else{
                console.log("push="+roleSum)
                roleArray[se.id].push(roleSum)
                hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
            }
        }else{
            console.log(se.id+" is false")
            roleArray[se.id] = []
            roleArray[se.id].push(roleSum)
            hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
        }
        hiddenItem.value = selectedOption.value;
    
        //console.log(roleArray[se.id])
        
        // xボタンをクリックしたら削除するように仕込む
        removeBtn.addEventListener("click", function () {
            // 削除する要素の番号
            let roleObjName = hiddenItem.name.substring(hiddenItem.name.lastIndexOf("_") + 1);
            
            roleArray[se.id][roleObjName - 1] = null
            item.remove();
            hiddenItem.remove();
            selectedOption.selected = false;
        });
        
        item.appendChild(removeBtn);
        selectedItems.appendChild(item);
        selectedItems.appendChild(hiddenItem)
    });
}
*/

const selectAddEvent = (se) => {
    let selectId = document.getElementById(se.id);

    // チャンネルidのみを引き出す
    const divId =se.id.substring(se.id.indexOf("_") + 1) 

    function addSelectEvent(e) {
        const selectedItems = document.getElementById(divId);

        // 二重に登録されないように削除
        selectId.removeEventListener("change",addSelectEvent); // change属性を削除する

        const selectedOption = e.target.selectedOptions[0];
    
        const outerTextIndex = selectedItems.outerText.indexOf(selectedOption.textContent);
        
        if (outerTextIndex !== -1){
            console.log("return")
            return
        }
    
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
        
        if (roleArray[se.id]){
            console.log(se.id+" is true")
            if (roleArray[se.id].includes(roleSum)){
                let arrayNull = roleArray[se.id].indexOf(null)
                console.log("uwagaki="+arrayNull)
                if (arrayNull > -1){
                    hiddenItem.name = "role_" + selectedItems.id + "_" +(arrayNull + 1);
                    roleArray[se.id][arrayNull] = (arrayNull + 1)
                }
            }else{
                console.log("push="+roleSum)
                roleArray[se.id].push(roleSum)
                hiddenItem.name = "role_" + selectedItems.id + "_" + roleSum;
            }
        // ロールの中身が空
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
            let roleObjName = hiddenItem.name.substring(hiddenItem.name.lastIndexOf("_") + 1);
            
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



// 既存要素の削除
const removeAdd = (removeItem) => {
    //.parentNodeで親要素の指定
    removeItem.parentNode.remove()
}