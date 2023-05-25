let confirmBtn = document.querySelector("#confirmModal a[href='#']")

$('a[data-bs-target="#confirmModal"]').click(e => {
    confirmBtn.href = e.currentTarget.href
    return false
})