function Project(name){
	this.name = name;
	this.trackMap = {};
	this.libraryClipMap = {};
	this.clipMap = {};
	this.currentUsersMap = {};
}

Project.prototype.rename = function(newName){
	this.name = newName;
}

Project.prototype.newTrack = function(trackName){
	this.trackMap[trackName] = new Track(trackName);
}

//for testing   
Project.prototype.newLibraryClip = function(filename){
	this.libraryClipMap[filename] = new LibraryClip(filename);
}
/*
Project.prototype.deleteLibraryClip = function(filename){
	delete this.libraryClipMap[filename];
}

Project.prototype.renameLibraryClip = function(filename, newName){
	this.libraryClipMap[newName] = this.libraryClipMap[filename];
	delete this.libraryClipMap[filename];
}
*/

/* Makes a new Clip and adds it to the Track.  Call this after server returns with a clipID. */
Project.prototype.addClipToTrack = function(trackName, clipID, position, libraryClipFileName, startTime, endTime){
   console.log(endTime)
    var clip = new Clip(trackName, clipID, position, libraryClipFileName, startTime, endTime);
	this.trackMap[trackName].addClip(clipID, clip);	
	this.clipMap[clipID] = clip;
    	// Load audio resource, if needed (see play.js)
	load_clip(libraryClipFileName);
}

Project.prototype.deleteClip = function(clipID){
	delete this.trackMap[this.clipMap[clipID].trackName].clipMap[clipID];
	delete this.clipMap[clipID];
}

Project.prototype.moveClip = function(clipID, newStartTime){
	this.clipMap[clipID].position = newStartTime;
}

Project.prototype.cloneClip = function(oldClipID, trackName, position, newClipID){
	var clip = this.clipMap[oldClipID];
    this.addClipToTrack(trackName, newClipID, position, clip.filename, clip.startTime, clip.endTime)
    onmessage("addClipToTrack", [trackName, newClipID, position, clip.filename, clip.startTime, clip.endTime]);
}


Project.prototype.splitClip = function(clipID, splitTime){
	
}

Project.prototype.joinClips = function(clipID1, clipID2){
	
}

Project.prototype.trimClip = function(clipID, newStartTime, newEndTime){
	this.clipMap[clipID].position = String(parseFloat(newStartTime) - parseFloat(this.clipMap[clipID].startTime) +parseFloat(this.clipMap[clipID].position)); 
	this.clipMap[clipID].startTime = newStartTime;
    this.clipMap[clipID].endTime = newEndTime;
    this.clipMap[clipID].length = newEndTime - newStartTime;

}

Project.prototype.setTrackVolume = function(trackName, newValue){
	
}

Project.prototype.setTrackPanning = function(trackName, newValue){
	
}

Project.prototype.lockClip = function(clipID) {
    this.clipMap[clipID].locked = 1;
}
Project.prototype.tempLock = function(clipID) {
    this.clipMap[clipID].tempLock = 1;
}
Project.prototype.tempUnlock = function(clipID) {
    this.clipMap[clipID].tempLock = 0;
}

Project.prototype.unlockClip = function(clipID) {
    this.clipMap[clipID].locked = 0;
    this.clipMap[clipID].lockedByMe = 0;
}
Project.prototype.grantClipLock = function(clipID) {
    this.clipMap[clipID].lockedByMe = 1;
}
Project.prototype.lockTrack = function(track) {
    this.trackMap[track].locked = 1;
}
Project.prototype.unlockTrack = function(track) {
    this.trackMap[track].locked = 0;
    this.trackMap[track].lockedByMe = 0;
}
Project.prototype.grantTrackLock = function(track) {
    this.trackMap[track].lockedByMe = 1;
}

Project.prototype.addUser = function(username, color) { //color is a hex color value string
	this.currentUsersMap[username] = color;
}

Project.prototype.removeUser = function(username) {
	delete this.currentUsersMap[username];
}

function Track(name){
	this.name = name;
	this.clipMap = {};
	this.volume = 100;
	this.panning = 50;
    this.locked = 0;
    this.lockedByMe = 0;
}

Track.prototype.addClip = function(clipID, clip){
	this.clipMap[clipID] = clip;
}


function LibraryClip(filename){
	this.filename = filename;
	this.startTime = 0;
	//TODO: get endTime
}

LibraryClip.prototype.getFileName = function(){
	return this.filename;
}

function Clip(trackName, clipID, position, fileName, startTime, endTime){
	this.trackName = trackName;
	this.clipID = clipID;
	this.filename = fileName;
	this.position = position;
	this.startTime = startTime;
	this.endTime = endTime;
    this.length = endTime - startTime;
    this.origLength = endTime - startTime;
    this.locked = 0;
    this.lockedByMe = 0;
    this.tempLock = 0;
}

Clip.prototype.getID = function(){
	return this.clipID;
}
Clip.prototype.getPosition = function(){
	return this.position;
}

Clip.prototype.getLibraryClipStartTime = function(){
	return this.startTime;
}

Clip.prototype.getLibraryClipEndTime = function(){
	return this.endTime;
}
Clip.prototype.getLength = function(){
	return this.length;
}
Clip.prototype.getFileName = function(){
	return this.filename;
}
