let bttbtn = document.getElementById("back-to-top-btn");

window.addEventListener("scroll", () => {
    const THRESHOLD = 400
    if (
        document.body.scrollTop > THRESHOLD ||
        document.documentElement.scrollTop > THRESHOLD
    ) {
        bttbtn.style.display = "block";
    } else {
        bttbtn.style.display = "none";
    }
})

function backToTop() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}

bttbtn.addEventListener("click", backToTop);
