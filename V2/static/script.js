window.onload = function () {
	document.getElementById("addsong").addEventListener("click", duplicate);
	document.getElementById("removesong").addEventListener("click", remove);
}

var count = 1;
function duplicate() {
	count++;
	var inputs = document.getElementById("inputs");
	var input = document.createElement("div");
	input.innerHTML = '<input autocomplete="off" autofocus name="track_name' + count + '" placeholder="Title" type="text"><input autocomplete="off" autofocus name="artist' + count + '" placeholder="Artist" type="text">'
	
	inputs.appendChild(input)
	
	if (count >= 5) {
		document.getElementById("addsong").style.display = "none";
	}
	if (count <= 5) {
		document.getElementById("removesong").style.display = "block";
	}
}

function remove() {
	count--;
	var inputs = document.getElementById("inputs");
	inputs.removeChild(inputs.lastChild);
	
	if (count < 5) {
		document.getElementById("addsong").style.display = "block";
	} 
	if (count == 1) {
		document.getElementById("removesong").style.display = "none";
	}
}