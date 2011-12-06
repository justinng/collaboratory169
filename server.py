import logging
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import mimetypes
from py.AudioUtil import *
from py.ProjectInstance import *


from tornado.options import define, options
mimetypes.add_type("audio", "wav")
mimetypes.add_type("image", "jpg")
mimetypes.add_type("image", "png")
define("port", default=8093, help="run on the given port", type=int)
#change this to change source html file:
source = "projectGUI.html"
#source = "flashtest.html"
source = "profilepage.html"
#uncomment the following line to try the test
#source = "test_dispatch.html"


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [  (r"/(.+\.html)?", MainHandler), (r"/project/(.+)/(.+)", ProjectHandler), (r"/ws", SocketHandler), (r"/upload/(.+)/(.+)", UploadHandler), (r"/templates/(.*)", TemplateHandler), (r"/login", LoginHandler)]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
	    autoescape=None,	
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self, file):
        if file:
            self.render(file)
        else:
            self.render(source)

class ProjectHandler(tornado.web.RequestHandler):
    def get(self, bandname, projname):
        self.render("projectGUI.html", band=bandname, proj=projname)

class UploadHandler(tornado.web.RequestHandler):
    def post(self, band, project):
       #store audio clip
        recording = False
        logging.info("Upload "+band+" "+project)
        if not (session.getBand(band) and session.getBand(band).getProject(project)):
                logging.info("project is not open")
                return
        if 'audio' not in self.request.files: #upload is a recording
            recording = True
            body = self.request.body
            proj = session.getBand(band).getProject(project)
            filename = self.request.headers['filename']+".wav";
            #recordingCounter = proj.newRecording()
            #filename = "recording"+str(recordingCounter)+".wav"
        else:                                  #upload is a normal file
            file=self.request.files['audio'][0]
            filename = file['filename']
            body = file['body']
        if filename.split('.')[-1] != 'wav':
                logging.info("File is not a .wav")
        	return
        filename=os.path.basename(filename)
        logging.info("Upload sent: " + filename)
        if session.getBand(band) and session.getBand(band).getProject(project):
            dir_path = os.path.join(os.path.dirname(__file__), "static", "music", band, project)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            path = os.path.join(dir_path, filename)
            if True:#if not os.path.exists(path): #temporary solution to duplicate filenames
                open(path, 'w').write(body)
                waiter = list(SocketHandler.waiters[band][project])[0] #get an arbitrary waiter; kludge
                print "waiter"
                #print waiter
                #SocketHandler.send_updates(waiter, "newLibraryClip: "+filename)
                SocketHandler.newLibraryClipMessage(waiter, "newLibraryClip", [filename], "newLibraryClip: "+filename)
                if recording:
                    action = "addClipToTrack"
                    selectedTrack = self.request.headers['track']
                    position = self.request.headers['position']
                    args = [selectedTrack, position, filename]
                    argstring = "\', \'".join(args)
                    argstring = "(\'"+argstring+"\')"
                    eval_string="self.proj."+action+argstring
                    SocketHandler.addClipToTrackMessage(waiter, args, eval_string, action+": "+",".join(args))
                logging.info("Uploading file: "+path)
                logging.info("Length of uploaded wav is: %(duration)s ms" % {"duration": getWaveFileDuration(path)})

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("splash.html", imgsrc = "/images/Chrysanthemum.jpg")

class TemplateHandler(tornado.web.RequestHandler):
    def get(self, file):
        source=file
        #self.render(file)

class SocketHandler(tornado.websocket.WebSocketHandler):
    allowable_actions = 'newTrack newLibraryClip deleteLibraryClip addClipToTrack deleteClip moveClip cloneClip splitClip joinClips trimClip unlockClip unlockTrack addUser'.split()
    waiters = dict(); # a two-dimensional dict. The first has keys of bandnames. The second has keys of projnames. The values of these is a set for each project
    def open(self):
    	#SocketHandler.waiters.add(self)
        logging.info("WebSocket opened")
        self.username = "user";
        self.lockedClipIDs = [];
        self.lockedTrackNames = [];
        #new project
        
    def on_message(self, message):
        logging.info("received message %r", message)
        action = message.split(': ')[0]
        args = message.split(': ')[1].split(',')
        argstring = "\', \'".join(args)
        argstring = "(\'"+argstring+"\')"
        eval_string="self.proj."+action+argstring
        if action == "info":
            SocketHandler.processInfo(self, args)
        elif self.proj == None or self.band == None:
            logging.error("Attempted to send updates to a nonexistent project")
            return
        elif action == "lockClip":
            SocketHandler.lockClipMessage(self, args[0], args, message)
        elif action == "lockTrack":
            SocketHandler.lockTrackMessage(self, args[0], args, message)
        elif action == "refresh":
            SocketHandler.refreshClient(self)
        elif action == "addClipToTrack":
            SocketHandler.addClipToTrackMessage(self, args, eval_string, message)
        elif action == "cloneClip":
            SocketHandler.cloneClipMessage(self, args, eval_string, message)
        elif action == "newLibraryClip":
            self.newLibraryClipMessage(action, args, message)
        elif action == "addUser":
            self.addUserMessage(args, eval_string, message)
        elif action in self.allowable_actions and eval(eval_string):
        	SocketHandler.send_updates(self, message)
        else:
        	self.write_message("reject: "+message)
        
		
    def send_updates(self, msg, who="all"):
        logging.info("sending message:" + msg)
        if who == "self" or who == "all":
            self.write_message(msg) #just to decrease latency for the client making the change
        if who == "all" or who == "others":
            for waiter in self.waiters[self.bandname][self.projname]:
                if waiter == self:
                	continue
                waiter.write_message(msg)


    def refreshClient(self):
        for library_clip_name in self.proj._Project__libraryClipMap:
            libraryClip = self.proj._Project__libraryClipMap[library_clip_name]
            self.write_message("newLibraryClip: "+libraryClip.getName())
        for track_name in self.proj._Project__trackMap:
            track = self.proj._Project__trackMap[track_name]
            self.write_message("newTrack: "+track_name)
            self.write_message("setTrackVolume: " + track_name + ',' + str(track._Track__volume))
            self.write_message("setTrackPanning: " + track_name + ',' + str(track._Track__panning))
            if track._Track__locked:
                self.write_message("lockTrack: "+track_name)
            for clip in track._Track__clipsSet:
                args = [ track_name, str(clip._Clip__clipID), str(clip._Clip__position), clip._Clip__source._LibraryClip__name, str(clip._Clip__startTime), str(clip._Clip__endTime) ]
                argstring = ','.join(args)
                self.write_message("addClipToTrack: " + argstring)
                if clip._Clip__locked:
                    self.write_message("lockClip: "+str(clip._Clip__clipID))

    def addUserMessage(self, args, eval_string, message):
        color = eval(eval_string)
        self.username = args[0]
        self.send_updates(message + "," + color, "all")
        
    def lockClipMessage(self, clipID, args, message):
        #args.append(self.username)
        argstring = "(\'" + "\', \'".join(args) + "\')"
        eval_string = "self.proj.lockClip"+argstring
        if eval(eval_string):
            self.lockedClipIDs.append(clipID)
            SocketHandler.send_updates(self, message, "others")
            SocketHandler.send_updates(self, "grantClipLock: "+clipID, "self")

    def lockTrackMessage(self, track, args, message):
        #args.append(self.username)
        argstring = "(\'" + "\', \'".join(args) + "\')"
        eval_string = "self.proj.lockTrack"+argstring
        if eval(eval_string):
            self.lockedTrackNames.append(track)
            SocketHandler.send_updates(self, message, "others")
            SocketHandler.send_updates(self, "grantTrackLock: "+track, "self")


    def newLibraryClipMessage(self, action, args, message):
        #if newLibraryClip() succeeds...
        #if eval("self.proj.newLibraryClip(\"music/%(bandName)s/%(projectName)s/%(fileName)s\", args[0])" % {"bandName": self.bandname, "projectName": self.projname, "fileName": args[0]}):
        filename = args[0]
        path = os.path.join(os.path.dirname(__file__), "static", "music", self.bandname, self.projname, filename)
        if eval("self.proj.newLibraryClip(r\""+path+"\",\""+filename+"\")"):
            self.send_updates(message)
        else:
            self.write_message("reject: " + message)

    def addClipToTrackMessage(self, args, eval_string, message):
        trackname = args[0]
        position = args[1]
        libraryClipFileName = args[2]
        libraryClip = self.proj._Project__libraryClipMap[args[2].encode("utf-8")]
        startTime = "0"
        endTime = str(libraryClip.getLength())
        args = [trackname, position, libraryClipFileName, startTime, endTime]
        argstring = "\', \'".join(args)
        argstring = "(\'"+argstring+"\')"
        eval_string="self.proj."+"addClipToTrack"+argstring
        clipID = eval(eval_string)
        if clipID:
            message = "addClipToTrack: "+trackname+','+str(clipID)+','+position+','+libraryClipFileName+','+startTime+','+endTime
            SocketHandler.send_updates(self, message)
        else:
            self.write_message("reject: "+message)
        return

    def cloneClipMessage(self, args, eval_string, message):
        clipID = eval(eval_string)
        if clipID:
            message = message+","+str(clipID)
            SocketHandler.send_updates(self, message)
        else:
            self.write_message("reject: "+message)
            logging.info("sending message:" + message)
        return

    def processInfo(self, args):
        self.bandname, self.projname = args
        if not session.getBand(self.bandname) or not session.getBand(self.bandname).getProject(self.projname):
            session.load(self.bandname, self.projname)
        self.band = session.getBand(self.bandname)
        self.proj = self.band.getProject(self.projname)
        if self.bandname not in self.waiters:
            self.waiters[self.bandname] = dict({ self.projname : set() })
        elif self.projname not in self.waiters[self.bandname]:
            self.waiters[self.bandname][self.projname] = set()
        self.waiters[self.bandname][self.projname].add(self)
        self.inWaiters = True
        
    def on_close(self):
    	if self.inWaiters:
            SocketHandler.waiters[self.bandname][self.projname].remove(self)
            
            # release all owned locks
            for clipID in self.lockedClipIDs:
                self.proj.unlockClip(clipID)
                self.send_updates("unlockClip: " + clipID, "others")
            for trackName in self.lockedTrackNames:
                self.proj.unlockTrack(trackName)
                self.send_updates("unlockTrack: " + trackName, "others")
                
            # tell others that you are leaving
            self.proj.removeUser(self.username)
            self.send_updates("removeUser: " + self.username, "others")
                
            # unload project from memory if nobody else is using it
            if not SocketHandler.waiters[self.bandname][self.projname]:
                session.unload(self.bandname, self.projname)
                logging.info("Unloaded project: " + self.projname + " BY " + self.bandname)
        logging.info("WebSocket closed")

    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        self.stream = request.connection.stream
        self.ws_connection = None
        self.proj = None
        self.band = None
        self.bandname = ""
        self.projname = ""
        self.inWaiters = False


def main(): 
	tornado.options.parse_command_line()    
	app = Application()
    	app.listen(options.port)
	logging.info("starting ioloop")
    	tornado.ioloop.IOLoop.instance().start()

session = SessionManager()

main()

