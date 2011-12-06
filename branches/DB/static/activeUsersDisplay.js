function addUser(username, color){
	$("#usersDisplay").append(
			"<div id='user" + username.replace(new RegExp('.', 'g'),'__') + "' title='" + username + "' class='userDisplayEntry'>" +
			"<div style='width: 8px; height: 8px; border: 1px solid black; margin: 8px; float: left; background-color: " + color + ";'></div>" +
			"<span class='userName' style='font-size:12pt;float:left;'> " + username + " </span></div>"
			);
}

function removeUser(username){
	$("#user" + username.replace(new RegExp('.', 'g'),'__')).remove();
}