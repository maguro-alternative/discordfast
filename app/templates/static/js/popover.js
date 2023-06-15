const popoverBtn = document.getElementById('popover-btn');
const popoverContent = document.getElementById('popover-content');

popoverBtn.addEventListener('click', function() {
  //console.log(popoverContent.style.display)
  if (popoverContent.style.display === 'block'){
    popoverContent.style.display = 'none';
  }else if (popoverContent.style.display === 'none' || popoverContent.style.display == ''){
    popoverContent.style.display = 'block';
  }
});

