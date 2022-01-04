window.onload = function () {
	document.getElementById("rate").addEventListener("click", check_radio)
}

function check_radio(event) {
	wrapper = document.getElementById("rating");
	for (var i = 0; i < wrapper.childElementCount; i++) {
		if (wrapper.childNodes[i].firstElementChild.checked) {
			return 0;
		}
	}
	event.preventDefault();
}