function addClipToTrack(track, clipID, pos, clipName, startTime, endTime){
	libraryClip = $("#clip"+String(clipName).split("\.")[0].replace(new RegExp(' ', 'g'),'_')).html()
	trackClip = "<div id='clip"+String(clipID)+"' class='clip'>"+libraryClip+"</div>"
    $("#"+convertTrackNameServerToClient(track)).append(trackClip);
	$("#clip"+String(clipID)).css("position", "absolute");

	// Starting position (where you drop the clip)
	$("#clip"+String(clipID)).css("left", secondsToPixels(pos));
	
	// Set a clip's GUI width proportional to its running length
	var length = proj.clipMap[clipID].length;
	$("#clip"+String(clipID)).css("width", Math.floor(secondsToPixels(length)));
	
	// Allow a clip to be movable within a track
	$(".clip").draggable({
		snap: true,
		axis: 'x',
		helper: 'original',
		containment: [170],
		scroll: true,
		stop: overDragHandler
		});

    // Make the clip resizable; multipy by ratio from slider
	$("#clip" + String(clipID)).resizable({
		handles: 'e, w',
		maxWidth: $("#clip" + String(clipID)).width(),
		minWidth: 3,
		stop: resizeHandler
        });
    $("#clip" + String(clipID)).click(clipLockHandler);
    $("#clip" + String(clipID)).bind("dragstart", clipLockHandler);
    $("#clip" + String(clipID)).bind("dragstop", clipLockHandler);
    $("#clip" + String(clipID)).bind("resizestart", clipLockHandler);
    $("#clip" + String(clipID)).bind("resizestop", clipLockHandler);
    if (proj.trackMap[track].locked) {
      $("#clip" + String(clipID)).draggable( "option", "disabled", true );
      $("#clip" + String(clipID)).resizable( "option", "disabled", true );
    }

    function clipLockHandler(e, ui) {
        var clip = proj.clipMap[this.id.slice(4)];
        if (clip.locked) {}
        else if (clip.lockedByMe && e.type == "click" 
                 || ((e.type == "dragstop" || e.type == "resizestop") && clip.tempLock)) {
            proj.tempUnlock(clip.getID());
            tellServer("unlockClip", clip.getID())
        }
        else if (e.type == "click") {
            if (!proj.trackMap[clip.trackName].locked) {
                tellServer("lockClip", clip.getID());
            }
        }
        //possible concurrency issue: if client starts dragging but the lock gets rejected, the clip might be in the wrong place. test this!
        else if ((e.type == "dragstart" || e.type == "resizestart") && !clip.lockedByMe) {
            proj.tempLock(clip.getID());
            tellServer("lockClip", clip.getID());
        }
        e.stopPropagation();
    }   
}


function posCorrect(pos, direction) {
			if(direction == "back") {
				return pos - 170;
			} else if (direction == "forward") {
				return pos + 170;
			} else {
				alert("incorrect posCorrect argument. pos = "+pos+"dir = "+direction)
			}
		}
