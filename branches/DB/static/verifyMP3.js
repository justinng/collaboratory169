function verifyMP3()
{
	input = document.forms["fileForm"]["audio"].value;
	subDis = document.forms["fileForm"]["submitName"];
	subDis.disabled = true;
	var patt = /.mp3$/g;
	if(patt.test(input)) {
		subDis.disabled = false;
	} else {
		alert("Invalid filetype.  Please submit a .mp3 file to upload");
		subDis.disabled = true;
	}
}	

