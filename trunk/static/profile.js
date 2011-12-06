// JavaScript for Profile page *to be merged with other js file*

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

