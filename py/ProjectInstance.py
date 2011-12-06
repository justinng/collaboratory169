'''
Created on Oct 15, 2011

@author: Justin

Definitions for back-end Project Instance Module classes.
'''

import os
import threading

import logging

from py.AudioUtil import *

class SessionManager(object):
    '''
    Master class for accessing all other project instance elements.
    Singleton.
    '''
    
    class __Singleton:
        ''' Implementation of the singleton interface '''

    # storage for the instance reference
    __instance = None

    def __init__(self, db):
        ''' Create singleton instance '''
        # Check whether we already have an instance
        if SessionManager.__instance is None:
            # Create and remember instance
            SessionManager.__instance = SessionManager.__Singleton()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = SessionManager.__instance
        
        self.__bandMap = {}
        self.__bandMapLock = threading.Lock()
        self.__db = db

    def __getattr__(self, attr):
        ''' Delegate access to implementation '''
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        ''' Delegate access to implementation '''
        return setattr(self.__instance, attr, value)
    
    '''
    Actual SessionManager implementation starts here
    '''
   
    def load(self, bandName, projectName):
        '''
        Loads the specified project.  If project does not exist, a new one is created.
        '''
        self.__bandMapLock.acquire()
        if bandName not in self.__bandMap:
            self.__bandMap[bandName] = BandManager(bandName)
        bandManager = self.__bandMap[bandName]
        self.__bandMapLock.release()
        
        return bandManager._load(projectName, self.__db)
    
    def unload(self, bandName, projectName):
        '''
        Unloads the Project from memory, and the BandManager as well if it no longer contains any Projects.  Assumes that there are no clients using the project!
        '''
        if bandName in self.__bandMap:
            bandManager = self.__bandMap[bandName]
            bandManager._unload(projectName)
            
            # remove BandManager from __bandMap if it is empty
            if bandManager._isEmpty():
                self.__bandMapLock.acquire()
                del self.__bandMap[bandName]
                self.__bandMapLock.release()
        return
    
    def save(self, bandName, projectName):
        '''
        Saves the specified project to the database, or does nothing if project is not in memory.  Returns success boolean.
        '''
        bandManager = self.__bandMap[bandName]
        if bandManager:
            return bandManager._save(projectName, self.__db)
        else:
            return False
    
    def getBand(self, bandName):
        '''
        Returns the specified BandManager, or False if it does not exist (which only occurs if that band has no projects loaded).
        '''
        if bandName in self.__bandMap:
            return self.__bandMap[bandName]
        else:
            return False

class BandManager(object):
    '''
    Contains all the Projects for a band.
    '''
    
    def __init__(self, bandName):
        self.__bandName = bandName
        self.__projectMap = {}
        self.__projectMapLock = threading.Lock()
        
    def _load(self, projectName, db):
        '''
        Ensures that the specified project is loaded.  If project does not exist, a new one is created.
        '''
        if projectName not in self.__projectMap:
            
            # create new Project
            self.__projectMapLock.acquire()
            project = Project(projectName)
            self.__projectMap[projectName] = project
            
            #check if database has info for existing project (if not, skip and return new project)
            projectQuery = db.get("SELECT P.ID, P.files FROM Project P, BandOwnsProjects O WHERE O.bandName = \"%(bandname)s\" AND P.name = \"%(projectname)s\"" % {"bandname":self.__bandName, "projectname":projectName})
            
            # if project exists in database...
            if projectQuery:
                
                projectID = projectQuery.ID
                projectFiles = projectQuery.files
                logging.info("Loading project (ID: %(id)i) from the database" % {"id":projectID})
                
                # load all library clips
                
                if (projectFiles):
                    for fileName in projectFiles.split("<>"):
                        print("making library clip: " + "%(COLdirectory)s\\static\\music\\%(bandname)s\\%(projname)s\\%(filename)s" % {"COLdirectory":os.path.split(os.path.dirname(__file__))[0], "bandname":self.__bandName, "projname":projectName, "filename":fileName})
                        project.newLibraryClip("%(COLdirectory)s/static/music//%(bandname)s//%(projname)s//%(filename)s" % {"COLdirectory":os.path.split(os.path.dirname(__file__))[0], "bandname":self.__bandName, "projname":projectName, "filename":fileName}, fileName)
                    
                # load all tracks/clips
                for track in db.query("SELECT * FROM Track T WHERE T.projectID = %(projectid)i" % {"projectid":projectID}):
                    # create Tracks
                    project.newTrack(track.name, track.volume, track.panning)
                    # add Clips to Tracks
                    for clipInfo in track.clips.split(","):
                        if(clipInfo):
                            clipParameters = clipInfo.split("|")
                            project.addClipToTrack(track.name, float(clipParameters[0]), clipParameters[1], float(clipParameters[2]), float(clipParameters[3]))
                        
            #if project is not in database, make a new, empty one
        self.__projectMapLock.release()
        return project
    
    def _unload(self, projectName):
        '''
        Unloads specified project from the __projectMap
        '''
        if projectName in self.__projectMap:
            self.__projectMapLock.acquire()
            del self.__projectMap[projectName]
            self.__projectMapLock.release()
            
        return
    
    def _save(self, projectName, db):
        '''
        Saves specified project to the database.  Returns True if save was successfully completed, or False if nothing was done.
        '''
        logging.info("Project %(projectname)s save initiated..." % {"projectname":projectName})
        
        if projectName in self.__projectMap:
            
            projectQuery = db.get("SELECT DISTINCT P.ID FROM Project P, BandOwnsProjects O WHERE O.bandName = \"%(bandname)s\" AND P.name = \"%(projectname)s\"" % {"bandname":self.__bandName, "projectname":projectName})
            existingProjectID = None
            if projectQuery:
                existingProjectID = projectQuery.ID
            project = self.__projectMap[projectName]
            
            oldTracksQuery = []
            # if project already exists in database...
            if existingProjectID:
                # get all globalIDs of old Track entries (to be deleted after save operation is finished)
                oldTracksQuery = db.query("SELECT T.globalID FROM Track T WHERE T.projectID = %(projectid)i" % {"projectid":existingProjectID})
                # update entry in Project table
                db.execute("UPDATE Project SET name = \"%(projectname)s\", files = \"%(libraryclipnames)s\" WHERE ID = %(projectid)i" % {"projectname":projectName, "libraryclipnames":project._getLibraryClipNames(), "projectid":existingProjectID})
            
            else:
                # create new entry in Project table, reassign existingProjectID
                existingProjectID = db.execute("INSERT INTO Project (name, files) VALUES (\"%(projectname)s\", \"%(libraryclipnames)s\")" % {"projectname":projectName, "libraryclipnames":project._getLibraryClipNames()})
                
                # add project under Band table
                db.execute("INSERT INTO BandOwnsProjects (bandName, ID) VALUES (\"%(bandname)s\", %(projectid)i)" % {"bandname":self.__bandName, "projectid":existingProjectID})
                
                # add project under every User
                for bandMemberTuple in db.query("SELECT M.email FROM MemberOf M WHERE M.bandName = \"%(bandname)s\"" % {"bandname":self.__bandName}):
                    db.execute("INSERT INTO UserOwnsProjects (email, ID) VALUES (\"%(email)s\", %(projectid)i)" % {"email":bandMemberTuple.email, "projectid":existingProjectID})
                
            for track in project._getTracks():
                # save all current tracks
                logging.info("Saving info into Track table")
                db.execute("INSERT INTO Track(projectID, name, clips, volume, panning) VALUES (%(projectid)i, \"%(trackname)s\", \"%(trackclipinfo)s\", %(volume)i, %(panning)i)" % {"projectid":existingProjectID, "trackname":track._getName(), "trackclipinfo":track._clipInfo(), "volume":track._getVolume(), "panning":track._getPanning()})
            
            # delete old Track entries in oldTracksQuery, if there are any
            for track in oldTracksQuery:
                db.execute("DELETE FROM Track WHERE globalID = %(globalid)i" % {"globalid":track.globalID})
                
            logging.info("Project %(projectname)s save completed" % {"projectname":projectName})
            
            return True
        
        else:
            logging.error("Project %(projectname)s does not exist in memory!" % {"projectname":projectName})
            return False
                
    def _isEmpty(self):
        '''
        Returns True if this BandManager contains no active Projects.
        '''
        if self.__projectMap:
            return False
        else:
            return True
        
    def getName(self):
        return self.__bandName
 
    def getProject(self, projectName):
        '''
        Returns the specified Project under this BandManager, or False if it does not exist.
        '''
        if projectName in self.__projectMap.keys():
            return self.__projectMap[projectName]
        else:
            return False

class Project(object):
    '''
    Fully specifies a project.
    '''
    
    def __init__(self, name):
        self.__name = name
        self.__trackMap = {}
        self.__trackMapLock = threading.Lock()
        self.__libraryClipMap = {}
        self.__libraryClipMapLock = threading.Lock()
        self.__clipMap = {}
        self.__clipMapLock = threading.Lock()
        self.__clipIDCounter = 1
        self.__clipIDCounterLock = threading.Lock()
        self.__recordingCounter = 1
        self.__recordingCounterLock = threading.Lock()
        self.__currentUsersMap = {}
        self.__availableUserColors = ["#C0C0C0", "#FF00FF", "#00FFFF", "#FFFF00", "#0000FF", "#00FF00", "#FF0000"]
        self.__usersLock = threading.Lock()  # use this lock for both currentUsersMap and availableUserColors
        
    def addUser(self, username):
        '''
        Adds a user to the current project session and assigns a color.
        Assumes the username is unique.
        '''
        color = ""
        self.__usersLock.acquire()
        if len(self.__availableUserColors) <= 0:
            color = "#000000"
        else:
            color = self.__availableUserColors.pop()
        self.__currentUsersMap[username] = color
        self.__usersLock.release()
        return color
        
    def removeUser(self, username):
        self.__usersLock.acquire()
        if username in self.__currentUsersMap.keys():
            self.__availableUserColors.append(self.__currentUsersMap[username])
            del self.__currentUsersMap[username]
            self.__usersLock.release()
            return True
        else:
            self.__usersLock.release()
            return False
        
    def getName(self):
        return self.__name
    
    def _getTracks(self):
        return self.__trackMap.values()
    
    def _getLibraryClipNames(self):
        libraryClipNamesList = []
        for libraryClipName in self.__libraryClipMap.keys():
            # append string in the following format: [position (in seconds)] [libraryClipName] [startTime] [endTime]
            libraryClipNamesList.append("<>")
            libraryClipNamesList.append(libraryClipName)
        
        if libraryClipNamesList:
            # remove leading "><" separator
            libraryClipNamesList.remove("<>")
        
        return "".join(libraryClipNamesList)
    
    def rename(self, newName):
        '''
        TODO: check DB for name collision
        '''
        return
    
    def exportSong(self):
        '''
        TODO
        '''
        return
        
    def newTrack(self, trackName, volume=100, panning=50):
        '''
        Add a new Track.  Returns success/failure.
        '''
        
        if trackName not in self.__trackMap.keys():
            self.__trackMap[trackName] = Track(trackName, volume, panning)
            return True
        else:
            return False
    
    def newLibraryClip(self, filepath, libraryClipName):
        '''
        Add a new LibraryClip.  The given libraryClipName should be unique, and the filepath should be valid.  Returns success/failure.
        '''
        if libraryClipName not in self.__libraryClipMap.keys() and os.path.exists(filepath):
            renderWaveform(filepath, libraryClipName)
            self.__libraryClipMap[libraryClipName] = LibraryClip(filepath, libraryClipName)
            return True
        else:
            print self.libraryClipMap.keys()
            return False
    
    def deleteLibraryClip(self, libraryClipName):
        '''
        Delete the LibraryClip from this Project, as well as its source file.  File must exist, and name must be in libraryCLipMap.  Returns success/failure.
        '''
        try:
            os.remove(self.__libraryClipMap[libraryClipName].__filepath)
        except OSError:
            #TODO: log absence of source file
            return False
        
        if libraryClipName in self.__libraryClipMap.keys():
            del self.__libraryClipMap[libraryClipName]
            return True
        else:
            return False
    
    def renameLibraryClip(self, libraryClipName, newName):
        '''
        Rename the LibraryClip.  Returns success/failure.
        '''
        # if LibraryClip is present, rename it and update the entry in libraryClipMap
        if libraryClipName in self.__libraryClipMap.keys():
            targetLibraryClip = self.__libraryClipMap[libraryClipName]
            targetLibraryClip._rename(newName)
            del self.__libraryClipMap[libraryClipName]
            self.__libraryClipMap[newName] = targetLibraryClip
            return True
        else:
            #TODO: log absence of LibraryClip
            return False
    
    def addClipToTrack(self, trackName, position, libraryClipName, startTime, endTime):
        '''
        Add a new instance of a Clip to the specified track at the specified position.  Returns the clip ID (clip IDs are assigned automatically) or False if unsuccessful.
        '''
        self.__libraryClipMapLock.acquire()
        self.__trackMapLock.acquire()
        if trackName in self.__trackMap and libraryClipName in self.__libraryClipMap.keys():
            # get Track
            track = self.__trackMap[trackName]
            self.__trackMapLock.release()
            # obtain a Clip ID to use, and increment counter
            self.__clipIDCounterLock.acquire()
            clipID = self.__clipIDCounter
            self.__clipIDCounter += 1
            self.__clipIDCounterLock.release()
            # create new Clip
            clip = Clip(clipID, track, self.__libraryClipMap[libraryClipName], position, startTime, endTime)
            self.__libraryClipMapLock.release()
            # add Clip to Track __clipMap
            track._addClip(clip)
            self.__clipMapLock.acquire()
            self.__clipMap[clipID] = clip
            self.__clipMapLock.release()
            return clipID
        else:
            return False
    
    def deleteClip(self, clipID):
        '''
        Delete the Clip with the specified clipID, if it exists on the timeline.  Returns success/failure.
        '''
        self.__clipMapLock.acquire()
        clipID = int(clipID)
        if clipID in self.__clipMap.keys():
            # delete Clip reference from __clipMap
            clip = self.__clipMap[clipID]
            del self.__clipMap[clipID]
            self.__clipMapLock.release()
            
            # delete Clip reference from Track
            clip._getTrack()._deleteClip(clip)
            
            return True
        else:
            return False
    
    def moveClip(self, clipID, newPosition):
        '''
        Moves the clip to a new place on the timeline.  Does nothing if the clip does not exist.
        '''
        clipID = int(clipID)
        if clipID in self.__clipMap.keys():
            self.__clipMap[clipID]._move(newPosition)
            return True
        return False
    
    def cloneClip(self, clipID, trackName, position):
        '''
        Creates a copy of the specified clip at the specified position.  Returns the clip ID of the new clip, or False if original clip does not exist.
        '''
        clipID = int(clipID)
        self.__clipMapLock.acquire()
        if clipID in self.__clipMap.keys():
            sourceClip = self.__clipMap[clipID]
            self.__clipMapLock.release()
            # obtain a Clip ID to use, and increment counter
            self.__clipIDCounterLock.acquire()
            clipID = self.__clipIDCounter
            self.__clipIDCounter += 1
            self.__clipIDCounterLock.release()
            # create new clip
            newClip = Clip(clipID, self.__trackMap[trackName], sourceClip._getLibraryClip(), position, sourceClip._getStartTime(), sourceClip._getEndTime())
            # add Clip to Track __clipMap
            self.__trackMap[trackName]._addClip(newClip)
            self.__clipMapLock.acquire()
            self.__clipMap[clipID] = newClip
            self.__clipMapLock.release()
            return clipID
        else:
            return False
    
    def splitClip(self, clipID, splitTime):
        '''
        Splits the specified clip by shortening the original to [startTime, splitTime] and making another with range [splitTime, endTime]
        Returns the clip ID of the second clip part; the first part retains the clip ID of the original.
        '''
        if clipID in self.__clipMap.keys():
            originalClip = self.__clipMap[clipID]
            originalEndTime = originalClip._getEndTime()
            
            # if the original clip's end time can be trimmed as specified...
            if originalClip._trim(originalClip._getStartTime(), originalClip._getEndTime()):
                return self.addClipToTrack(originalClip._getTrack()._getName(), originalClip._getPosition() + splitTime, originalClip._getLibraryClip().getName(), splitTime, originalEndTime)
        
        return False
    
    def joinClips(self, clipID1, clipID2):
        '''
        TODO
        '''
        return
    
    def trimClip(self, clipID, newStartTime, newEndTime):
        '''
        changes the start and end times of the library clip
        '''
        clipID = int(clipID)
        if clipID in self.__clipMap.keys():
            return self.__clipMap[clipID]._trim(newStartTime, newEndTime)
        else:
            return False
    
    def setTrackVolume(self, trackName, newValue):
        '''
        Sets the track's volume.
        '''
        if trackName in self.__trackMap.keys():
            self.__trackMap.keys()._setVolume(newValue)
        return
    
    def setTrackPanning(self, trackName, newValue):
        '''
        Sets the track's panning.
        '''
        if trackName in self.__trackMap.keys():
            self.__trackMap.keys()._setPanning(newValue)
        return
    def lockClip(self, clipID):
        clipID = int(clipID)
        if clipID in self.__clipMap.keys():
            return self.__clipMap[clipID]._lock()
    def unlockClip(self, clipID):
        clipID = int(clipID)
        if clipID in self.__clipMap.keys():
            return self.__clipMap[clipID]._unlock()
    def lockTrack(self, track):
        if track in self.__trackMap.keys():
            return self.__trackMap[track]._lock()
    def unlockTrack(self, track):
        if track in self.__trackMap.keys():
            return self.__trackMap[track]._unlock()
    def newRecording(self):
    	self.__recordingCounterLock.acquire()
        recordingID = self.__recordingCounter
        self.__recordingCounter += 1
        self.__recordingCounterLock.release()
        return recordingID

class Track(object):
    '''
    Represents a track in the project.
    '''
    def __init__(self, name, volume=100, panning=0):
        self.__name = name
        self.__clipsSet = set([])
        self.__volume = volume
        self.__panning = panning
        self.__locked = False
        
    def _getName(self):
        return self.__name
        self.__locked = False
    
    def _clipInfo(self):
        clipInfoStringList = []
        for clip in self.__clipsSet:
            # append string in the following format: [position (in seconds)]|[libraryClipName]|[startTime]|[endTime]
            clipInfoStringList.append(",")
            print(clip._getStartTime())
            print(clip._getEndTime())
            clipInfoStringList.append("%(position)s|%(libraryclipname)s|%(starttime)s|%(endtime)s" % {"position":clip._getPosition(), "libraryclipname":clip._getLibraryClip().getName(), "starttime":clip._getStartTime(), "endtime":clip._getEndTime()})

        if clipInfoStringList:
            # remove leading comma
            clipInfoStringList.remove(",")
        
        return "".join(clipInfoStringList)
    
    def _getVolume(self):
        return self.__volume
    
    def _getPanning(self):
        return self.__panning
    
    def _addClip(self, clip):
        self.__clipsSet.add(clip)
        return
    
    def _deleteClip(self, clip):
        if clip in self.__clipsSet:
            self.__clipsSet.remove(clip)
        return
    
    def _setVolume(self, newValue):
        self.__volume = newValue
        return
    
    def _setPanning(self, newValue):
        self.__panning = newValue
        return

    def _lock(self):
        if self.__locked:
            return False
        else:
            self.__locked = True
            return True
    def _unlock(self):
        if not self.__locked:
            return False
        else:
            self.__locked = False
            return True
        
    
class LibraryClip(object):
    '''
    Represents a library clip (from the library pane).
    '''
    def __init__(self, filepath, name):
        self.__name = name
        self.__filepath = filepath
        self.__length = getWaveFileDuration(filepath)
        
    def _rename(self, newName):
        self.__name = newName
        return
    def getName(self):
        return self.__name
    def getLength(self):
        return self.__length

class Clip(object):
    '''
    Represents a clip (from the timeline).
    '''
    def __init__(self, clipID, track, libraryClip, position, startTime, endTime):
        self.__clipID = clipID
        self.__track = track
        self.__source = libraryClip
        self.__position = position
        self.__startTime = 0
        self.__endTime = endTime
        self.__locked = False
        
    def _getID(self):
        return self.__clipID
        
    def _getTrack(self):
        return self.__track
    
    def _getLibraryClip(self):
        return self.__source
    
    def _getPosition(self):
        return self.__position
    
    def _getStartTime(self):
        return self.__startTime
    
    def _getEndTime(self):
        return self.__endTime

    def _lock(self):
        if self.__locked:
            return False
        else:
            self.__locked = True
            return True
    def _unlock(self):
        if not self.__locked:
            return False
        else:
            self.__locked = False
            return True

    def _move(self, newPosition):
        self.__position = newPosition
        return
    def _trim(self, newStartTime, newEndTime):
        if float(newStartTime) < 0 or float(newEndTime) > self.__source.getLength() or float(newStartTime) > float(newEndTime):
            return False
        self.__position = str(float(newStartTime) - float(self.__startTime) + float(self.__position))
        self.__startTime = newStartTime
        self.__endTime = newEndTime
        return True
