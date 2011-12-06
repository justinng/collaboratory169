$(document).ready(function() {





    $("input[type='range']").live('change',function() {
        var newValue = $(this).attr("value");
        $(this).siblings('.volRange').html(newValue);
        $(this).siblings('.player').volume=parseFloat(newValue/100);
    });


    $("#newTrack").click(function() {
        var trackName = prompt("Track name");
        if (trackName == null || trackName == "") {return;}
        var patt1=/[^\w\s]/;
		if (trackName.match(patt1)) {
			alert("Track name contains invalid characters");
			return;
		}
        tellServer("newTrack", trackName);
    });


});
