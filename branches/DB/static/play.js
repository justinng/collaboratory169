//This will not work well in Chrome! Use Firefox!


var audio = {};
var timeout = {};
var channelTimeout = {};
var play_state = 'stopped';
var snapshot;
var start_time;
var position = 0; // in seconds
var numChannels = 16;
var currentPosition = 0;
var scrollTimeout;

//array of Audio channels
var channels = new Array();
for (i = 0; i < numChannels; i++){
	channels[i] = new Object();
	channels[i].available = true;
	channels[i].timeout = 0;
	channels[i].audio = new Audio();
        channels[i].audio.onended = function(){
		channels[i].available = true;
	}
}


function play() {
	if (play_state == 'playing') {return;}
    else if (play_state == 'paused') {play_from_pause();}
    else if (play_state == 'stopped') {
        //setup_play();
        //play_from_pause();
        //function loaded() {console.log("shit!!"); play_from_pause();}
        //document.addEventListener("DOMContentLoaded", loaded, false);
        //setTimeout("play_from_pause()", 1000); //kludge - do this right!
    	//audio["1 lead.wav"].play();
    	play_from_pause();
    }


    else {alert("OH SHIT!! Fatal error!!!")}
}

/*
function setup_play() {
    play_state = 'paused';
    snapshot = proj.clipMap;
    for (clipID in snapshot)
        {
            clip = snapshot[clipID];
            audio[clipID] = document.createElement('audio');
            audio[clipID].setAttribute('src', '/static/music/'+bandname+'/'+proj.name+'/'+clip.getFileName());
            audio[clipID].load();
            //waitForLoad(audio[clipID]);
    }
}
*/

function load_clip(fileName) {
    if (!(fileName in audio))
    {
    	var clip = proj.libraryClipMap[fileName];
    	audio[fileName] = document.createElement('audio');
    	audio[fileName].preload = "auto";
    	audio[fileName].setAttribute('src', '/static/music/'+bandname+'/'+proj.name+'/'+clip.getFileName());
        //audio[fileName].load();
    }
}

function changeClipVolume(fileName, value){
	if (fileName in audio){
		audio[fileName].volume = value/100;
	}
}

function changeClipPanning(fileName, value){
	if (fileName in audio){
		
	}
}

function waitForLoad(audio) {
    function loadStart(event)
	{
    	console.log("1");
        audio.currentTime = 3;
    }
	function init()
	{
    	audio.addEventListener('loadedmetadata', loadStart, false);
	}
	document.addEventListener("DOMContentLoaded", init, false);
}

/*
function play_from_pause() {
    console.log("playing");
    play_state = 'playing';
    start_time = new Date();
    snapshot = proj.clipMap;  //TODO: this does not actually make a copy!
    for (clipID in snapshot)
        {
            clip = snapshot[clip_name];
            var offset = position - clip.getPosition();
            if (offset >= clip.getLength()) {continue;} //if the clip is done
            else if (offset < 0) { // if the clip has not started playing
                //waitForLoad(audio[clip_name]);
                //audio[clip_name].currentTime = clip.getLibraryClipStartTime();
                timeout[clip_name] = setTimeout("console.log('start'); audio['"+clip_name+"'].play()", -offset*1000);
            }
            else if (offset < clip.getLength()) { //if the position is in the middle of the clip
                //setupClip(clip.getLibraryClipStartTime() + offset, audio[clip_name]);
                audio[clip_name].currentTime = 3;
                audio[clip_name].currentTime = clip.getLibraryClipStartTime() + offset;
                audio[clip_name].play();
                //timeout[clip_name] = setTimeout("audio['"+clip_name+"'].play()", 0);
            }

            timeout[clip_name+"end"] = setTimeout ("console.log('" + clip_name + " '+'end'); audio['"+clip_name+"'].pause()",
                clip.getLength()*1000 - offset*1000);
        }
 }
 */
function play_from_pause() {
    console.log("playing at position " + String(currentPosition));
    play_state = 'playing';
    start_time = new Date();
    snapshot = proj.clipMap;  //TODO: this does not actually make a copy!
    for (var clipID in snapshot)
    {
            clip = snapshot[clipID];
            var offset = currentPosition - clip.getPosition();
            if (offset >= clip.getLength()) {continue;} //if the clip is done
            else if (offset < 0) { // if the clip has not started playing
                //timeout[clipID] = setTimeout("playClip(audio['" + clip.filename + "'], 0, " + String(clip.getLength() - offset) + ")", -offset*1000);
                playClip(audio[clip.filename], clip.startTime, clip.getLength() - offset, -offset*1000, clip.trackName);
            }
            else if (offset < clip.getLength()) { //if the position is in the middle of the clip
            	//timeout[clipID] = playClip(audio[clip.filename], parseFloat(clip.getLibraryClipStartTime()) + offset, parseFloat(clip.getLength()) - offset);
            	playClip(audio[clip.filename], parseFloat(clip.getLibraryClipStartTime()) + offset, parseFloat(clip.getLength()) - offset, 0, clip.trackName)
            }
            /*
            timeout[clipID+"end"] = setTimeout ("console.log('" + clipID + " '+'end'); audio['"+clipID+"'].pause()",
                clip.getLength()*1000 - offset*1000);
                */
        }
    start_time = new Date();
    for (i = 0; i < numChannels; i++)
    {
    	if (!channels[i].available)
    	{
    		timeout[i] = setTimeout("channels[" + i + "].audio.play();", channels[i].timeout);
    	}
    }
    scrollCursor();
 }

function playClip(audioObject, startTime, endTime, timeout, trackName){
	for (i = 0; i < numChannels; i++)
    {
		//console.log("starting "+String(i)+"th iteration");
    	if (channels[i].available)
    	{
    		channels[i].audio.src = audioObject.src;
    		channels[i].available = false;
    		channels[i].timeout = timeout;
    		channels[i].trackName = trackName;
    		channels[i].audio.volume = proj.trackMap[trackName].volume/100;
    		channels[i].audio.addEventListener('loadedmetadata', function(){
    			//console.log("eventhandler called.  i value is: "+String(i));
        		this.currentTime = startTime;
        		//this.play();
    			}, 
    			false);
		channels[i].audio.addEventListener('onended', function(){
    			this.available = true;
    		});
    		channels[i].audio.load();
    		channelTimeout[i] = setTimeout("console.log('pause');"+"channels[" + i + "].audio.pause(); channels[" + i + "].available = true", endTime*1000);
    		//console.log("audio loaded");
    		return;
    	}
    }
	
	alert("You have exceeded the maximum number of voices!  To get access to over 16 channels, please upgrade your subscription.");
}



function pause() {
    pause_time = new Date();
    for (clipID in snapshot)
    {
    	//clearTimeout(timeout[clipID]);
    }
    for (i = 0; i < numChannels; i++){
    	channels[i].audio.pause();
    	channels[i].available = true;
    	channels[i].timeout = 0;
    	clearTimeout(channelTimeout[i]);
    	clearTimeout(timeout[i]);
    }
    currentPosition = (pause_time.getTime() - start_time.getTime())/1000 + currentPosition;
    play_state = 'paused';
    //console.log("start time is "+ String(start_time.getTime()));
    //console.log("end time is   " + String(pause_time.getTime()));
    console.log("pausing at position "+String(currentPosition));
}
function stop() {
    pause();
    play_state = 'stopped';
/*    for (clipID in snapshot)
		{
            var audio_element = audio[clipID];
            audio_element.die();
	}*/
    timeout = {};
    channelTimeout = {};
    //audio = {};
    //snapshot = {};
    console.log("pos is " + position);
    currentPosition = position;
    $("#playbackCursor").css("left", String(position*sliderVal)+"px");
}


function scrollCursor() {
	if (play_state != 'playing') {
		clearTimeout(scrollTimeout);
		incrementCursor(-1);
		return;
	}
	var increment = 1000;
	var pixelsPerSecond = sliderVal;
	increment = 1000 / pixelsPerSecond;
	scrollTimeout = setTimeout("incrementCursor(1)", increment);
	var recursiveTimeout = setTimeout("scrollCursor()", increment);
}
function incrementCursor(increment) {
	var oldPos = $("#playbackCursor").css("left").slice(0,-2);
	var newPos = parseInt(oldPos) + increment;
	newPos = String(newPos)+"px";
	$("#playbackCursor").css("left", newPos);
}



var firstTime = false;
function record() {
    var lockCount = 0;
    var lockedTrack;
    for (track in proj.trackMap) {
         if (proj.trackMap[track].lockedByMe) {
             lockedTrack = track;
             lockCount += 1;
          }
    }
    if (lockCount != 1) {
        alert("You must select exactly one track in order to record");
        return;
    }
    var flash_record = document.getElementById("flash_record");
    flash_record.style.display = "block";
    setTimeout("document.getElementById('flash_record').record('"+lockedTrack+"','"+position+"'," + firstTime + ")", 500);
    if (firstTime) {firstTime = false;}
}
function hideFlash() {
    var flash_record = document.getElementById("flash_record");
    flash_record.style.display = 'none';
}
function setupRecord() {
    var swfVersionStr = "10.1.52";
    var xiSwfUrlStr = "";
    var flashvars = {};
    var params = {};
    flashvars.band = bandname;
    flashvars.project = projname;
    params.quality = "high";
    //params.bgcolor = "#ff0000";
    params.play = "true";
    params.loop = "false";
    params.wmode = "window";
    params.scale = "showall";
    params.menu = "false";
    params.devicefont = "false";
    params.salign = "";
    params.allowscriptaccess = "sameDomain";
    var attributes = {};
    attributes.id = "flash_record";
    attributes.name = "flash_record";
    attributes.align = "middle";
    swfobject.createCSS("html", "height:100%; background-color: white;");
    swfobject.createCSS("body", "margin:0; padding:0; overflow:hidden; height:100%;");
    swfobject.embedSWF(
        "/static/record.swf", "flashContent",
        "300", "150",
        swfVersionStr, xiSwfUrlStr,
        flashvars, params, attributes);
}
function traceFlash(text) {
    console.log("Flash: \""+text+"\"");
}
function FlashPromptName() {
    filename = prompt("Filename","recording");
    if (proj.libraryClipMap[filename+".wav"]) {
		alert("A file of that name already exists");
		FlashPromptName();
	}
    console.log(document.getElementById("flash_record"));
    document.getElementById("flash_record").upload(filename);
}
