// JavaScript for Profile page *to be merged with other js file*

var projects;
var insertToBand;

$(".bandName").toggle(function() {
		$(this).siblings(".projects").show();
		var temp = $(this).html();
		var bandname = temp.substring(2, temp.length);
		$(this).html("&darr; " + bandname); 
	}, 
	function() {
		$(this).siblings(".projects").hide();
		var temp = $(this).html();
		var bandname = temp.substring(2, temp.length);
		$(this).html("&rarr; " + bandname);
});

$("button.newband").click(function() {
    $("div#newBand").css({'top': '200px', 'left': '200px','display':'block'});
    $("div.blurify").css('opacity', '0.5');
});

$("img.addProject").click(function() {
    $("div#newProject").css({'top': '200px', 'left': '200px','display':'block'});
    $("div.blurify").css('opacity', '0.5');
    projects = $(this).siblings("ul").children("li a.projname").text();
    var temp = $(this).siblings("h4").text()
    insertToBand = temp.substring(2, temp.length);
});

$("img.deleteBand").click(function() {
    $("div#deleteBand").css({'top': '200px', 'left': '200px','display':'block'});
    $("div.blurify").css('opacity', '0.5');
    var bandName = $(this).attr("band");
    $("div#deleteBand input[name='bandName']").val(bandName);
});

$("button.cancel").click(function() {
    $("div#newBand, div#newProject, div#deleteBand").css({'top': '9999px', 'left': '0', 'display':'none'});
    $("div.blurify").css('opacity', "1.0");
    $("div#newBand span, div#newProject span").remove();
});

function sendProject(name) {
    $.ajax({
        type: 'POST',
        url: "/addproj",
        data: {projName : name, band : insertToBand},
        success: function() { //this is temporary [ask server to rerender page after adding to db]
            $("div#newProject").css({'top': '9999px', 'left': '0', 'display':'none'});
            $("div.blurify").css('opacity', "1.0");
            console.log("added");
            location.reload(true);
        }
    });
}

$("button.addproject").click(function() {
    var projName = $("input[name='projname']").val();
    if (projName == "") {
        $("#newProject").prepend("<span>Please provide a name</span>");
        return;
    }
    else {
        if (projects != "") {
            var temp = projects.indexOf(projName);
            if (temp > 0) {
                $("#newProject").prepend("<span>Project already exists</span>");
                return;
            }
            else {
                sendProject(projName);
            }
        }
        else { //now we can call the server
            sendProject(projName);
        }
    }

});

$("button.addband").click(function() {
    var bandNames = $("h4.bandName").text();
    var newName = $("input[name='name']").val();
    var temp = bandNames.indexOf(newName);
    if (newName == "") {
        $("#newBand").prepend("<span>Please provide a name</span>");
    }
    else { //send it via ajax.
        var people = $("input[name='add']").val();
        if (people == "") {
            people = "empty"
        }
        $.ajax({
            type: 'POST',
            url: "/profile",
            data: {bandName : newName, people : people},
            success: function(data) { //this is temporary [ask server to rerender page after adding to db]
                $("div#newBand").css({'top': '9999px', 'left': '0', 'display':'none'});
                $("div.blurify").css('opacity', "1.0");
                if (data) {
                    alert(data);
                    location.reload(true);
                }
                else {
                    location.reload(true);
                }
            }
        });

    }
});

