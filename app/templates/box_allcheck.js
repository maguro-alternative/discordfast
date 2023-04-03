function check(targetForm,flag,name){
    for (let n = 0;n <= targetForm.length - 1;n++) {
      if (targetForm.elements[n].type == "checkbox" && targetForm.elements[n].name.indexOf(name) >= 0) {
        targetForm.elements[n].checked = flag;
      }
    }
}