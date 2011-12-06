function verifyWAV()
{
	input = document.forms["fileForm"]["audio"].value;
	subDis = document.forms["fileForm"]["submitName"];
	subDis.disabled = true;
	var patt = /.wav$/g;
	if(patt.test(input)) {
		subDis.disabled = false;
	} else {
		alert("Invalid filetype.  Please submit a .wav file to upload");
		subDis.disabled = true;
	}
	if (proj.libraryClipMap[input]) {
		alert("A file of that name already exists");
		subDis.disabled = true;
		}
}	

