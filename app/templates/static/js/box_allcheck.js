function check(targetForm,flag,name){
    for (let n = 0;n <= targetForm.length - 1;n++) {
      if (targetForm.elements[n].type == "checkbox" && targetForm.elements[n].name.indexOf(name) >= 0) {
        targetForm.elements[n].checked = flag;
      }
    }
}

function classCheck(targetForm,flag,className){
  for (let i = 0;n < targetForm.length - 1;i++){
    if(targetForm.elements[i].type == "checkbox" && targetForm.elements[i].className.indexOf(className) >= 0){
      targetForm.elements[i].checked = flag;
    }
  }
}