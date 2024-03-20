function goToSelectedLink() {
    var select = document.getElementById("producers");
    var selectedOption = select.options[select.selectedIndex].value;
    if (selectedOption) {
        window.location.href = selectedOption;
    }
}