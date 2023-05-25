function setVar(name, value){
    $.ajax({
        type: "post",
        url: "/setvar",
        data: {
            name: name, 
            value: value,
            id: window.location.pathname.split('/')[2]
        },
    });
}


const collapseSwitch = document.getElementById('collapseSwitch')
collapseSwitch.addEventListener('change', event => {
  if (event.currentTarget.checked) {
    setVar("anj_collapse", "checked")
  } else {
    setVar("anj_collapse", "")
  }
})

const shuffleSwitch = document.getElementById('shuffleSwitch')
shuffleSwitch.addEventListener('change', event => {
  if (event.currentTarget.checked) {
    setVar("anj_shuffle", "checked")
  } else {
    setVar("anj_shuffle", "")
  }
})