function newLibraryClip(clipname, length){
    var clipsrc = "../music/band/proj/"+String(clipname)
	$("#library").append(
		"<div id='clip"+String(clipname).split("\.")[0].replace(new RegExp(' ', 'g'),'_') + 
				"' title='"+String(clipname).split("\.")[1]+"' class='libraryClip'>" +
			"<span class='clipName'>"+clipname+"</span>" +
			"<audio class='player' >" +
				"<source src="+clipsrc+" type='audio/wav' />" +
			"</audio>" +
		"</div>"
		);
	//$("#clip" + String(clipname).split("\.")[0]).draggable({
	var elementID = "clip" + String(clipname).split("\.")[0].replace(new RegExp(' ', 'g'),'_');
	$("#" + elementID).draggable({
		revert: true,
		helper: 'clone'
		});
} 