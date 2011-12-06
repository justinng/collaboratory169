function trackDropEventHandler(event, ui) {
	if (ui.draggable.is('.clip')){
		alert("It's a clip");
	} else if (ui.draggable.is('.libraryClip')) {
		alert("It's a library clip");
	} else {
		alert("Uh oh");
	}
}