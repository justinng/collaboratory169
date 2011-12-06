
var socket;


function openSocket() {    	
host = location.host;
    if ("WebSocket" in window) {
		socket = new WebSocket("ws://"+host+"/ws");
    } else {
        socket = new MozWebSocket("ws://"+host+"/ws");        
    }
	socket.onmessage = function(event) {
		message = event.data;
		action = message.split(': ')[0];
        args = message.split(': ')[1].split(',');
        if (action == "reject") {
        	alert(message);
        	return;
        	}
        argstring = args.join("\', \'");
        argstring = "(\'"+argstring+"\')";
        eval("proj."+action+argstring);
		onmessage(action, args);
		
	}
    socket.onopen = function(event) {
    	tellServer("info", bandname+','+projname)
        tellServer("refresh");
    	tellServer("addUser", username)
        setupRecord();
    }
}

//action is a string. args can be either an array 
//or a string separated by commas (no spaces)
function tellServer(action, args) {
    msg = action + ": " + args;
    socket.send(msg);
}
