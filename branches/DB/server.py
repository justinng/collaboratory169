import logging
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.database
import tornado.escape
import os.path
import mimetypes
from py.AudioUtil import *
from py.ProjectInstance import *


from tornado.options import define, options
mimetypes.add_type("audio", "wav")
mimetypes.add_type("image", "jpg")
mimetypes.add_type("image", "png")
define("port", default=8093, help="run on the given port", type=int)
define("mysql_host", default="107.20.135.212:3306", help="database host")
define("mysql_database", default="collaboratory", help="database name")
define("mysql_user", default="collaboratory", help="database user")
define("mysql_password", default="welcome", help="database password")
#change this to change source html file:
source = "projectGUI.html"
#source = "splash.html"
#source = "flashtest.html"
#source = "profilepage.html"
#uncomment the following line to try the test
#source = "test_dispatch.html"


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [  (r"/(.+\.html)?", MainHandler),
            (r"/ws", SocketHandler),
            (r"/upload/(.+)/(.+)", UploadHandler),
            (r"/templates/(.*)", TemplateHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/profile", ProfileHandler),
            (r"/addproj", AddProjectHandler),
            (r"/manage/([a-zA-Z0-9\s]+)", ManageBandHandler),
            (r"/signup", SignupHandler),
            (r"/profile/delete", BandDeleteHandler),
	        (r"/project/(.+)/(.+)/(.+)", ProjectHandler) ]

        settings = dict(
            #maybe change the secret later to be more secured
            cookie_secret= "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url= "/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
	    autoescape=None,	
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("coluser")
        if not user_id: return None
        return db.get("SELECT * FROM User WHERE ID = %s", int(user_id))


class MainHandler(BaseHandler):
    def get(self, file):
        if file:
            self.render(file)
        else:
#            self.render(source)
            self.redirect("/login")

class ProjectHandler(tornado.web.RequestHandler):
    def get(self, bandname, projname, username):
        self.render("projectGUI.html", band=bandname, proj=projname, user=username)

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

class SignupHandler(BaseHandler):
    def get(self):
        error = None
        self.render("signup.html", error=error)

    def post(self):
        name = self.get_argument("name", strip=True)
        email = self.get_argument("email", strip=True)
        password = self.get_argument("password", strip=True)
        confirm = self.get_argument("conpassword", strip=True)
        if not len(password) >= 4:
            self.clear()
            self.render("signup.html", error="Please provide a longer password.")
            return None
        #check if password matches
        if not password == confirm:
            self.clear()
            self.render("signup.html", error="Your password did not match.")
            return None
        #validate if new user
        validate = db.get("SELECT name FROM User WHERE email = %s", email)
        if validate:
            self.clear()
            #User already has account
            self.render("signup.html", error="Your are already registered")
            return None
        else:
            #lets put the user into the database.
            #encrypt the password
            encrypted = db.get("SELECT SHA1(%s) AS password", password)
            db.execute("INSERT INTO User (email, name, password) VALUES (%s, %s, %s)", email, name, encrypted.password)
            same = db.get("SELECT password from User where email=%s", email)
            self.render("thankyou.html", name=name)


class LoginHandler(BaseHandler):
    def get(self):
        self.render("splash.html", error=None)
        
    def post(self):
        email = self.get_argument("uname", strip=True);
        password = self.get_argument("pass", strip=True);
        encPassword = db.get("SELECT SHA1(%s) AS password", password)
        result = db.get("Select * from User where email= %s", email)
        if not result:
            self.clear()
            error = "we do not recognize you"
            self.render("splash.html", error=error)
            return None
        if encPassword.password == result.password:
            self.set_secure_cookie("coluser", str(result.ID))
            page = "/profile"
            self.redirect(page, permanent=False)
        else:
            self.clear()
            error = "your password did not match"
            self.render("splash.html", error=error)
            return None

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("coluser")
        self.redirect("/login", permanent=False)

class ManageBandHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, band):
        bandName = band
        members = db.query("SELECT u.name,u.email FROM User u, MemberOf m WHERE m.bandName = %s AND m.email = u.email", bandName)
        projects = db.query("SELECT p.name, p.ID FROM BandOwnsProjects b, Project p WHERE b.bandName = %s AND b.ID = p.ID", bandName)
        self.render("manage.html", band=bandName, members=members, projects=projects)

    def post(self, band):
        bandName = band
        try:
            addMembers = self.get_argument("add")
        except:
            addMembers = "empty"
        try:
            delMembers = self.get_arguments("delMembers")
        except:
            delMembers = "empty"
        try:
            delProjects = self.get_arguments("delProjects")
        except:
            delProjects = "empty"
        registered = db.query("SELECT email FROM User")
        registeredList = [ ] #put the queried result in a list
        for u in registered:
            registeredList.append(u.email)
        if (delMembers != "empty"):
            for member in delMembers:
                db.execute("DELETE FROM MemberOf WHERE email=%s AND bandName=%s", member, bandName)
        if (delProjects != "empty"):
            for project in delProjects:
                db.execute("DELETE FROM Project WHERE ID=%s", project)
        if (addMembers != "empty"):
            notAdded = ""
            members = addMembers.split(', ')
            for member in members:
                if (member in registeredList):
                    db.execute("INSERT INTO MemberOf (email, bandName) VALUES (%s, %s)", member, bandName)
                else:
                    notAdded += " "+member
            if not notAdded == "":
                self.write("These people are not added "+notAdded)
        self.redirect("/profile")


class AddProjectHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        projName = self.get_argument("projName")
        bandName = self.get_argument("band")
        db.execute("INSERT INTO Project (name) VALUES (%s)", projName) #insert to project table
        rowid = db.query("SELECT LAST_INSERT_ID() AS id") #get the id of the project that was inserted
        id = rowid.pop()
        db.execute("INSERT INTO BandOwnsProjects (bandName, ID) VALUES (%s, %s)", bandName, id.id)
        self.redirect("/profile", permanent=False)

class ProfileHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        param = self.get_current_user()
        bands = db.query("SELECT bandName FROM MemberOf WHERE email = %s", param.email)
        owns = db.query("SELECT name FROM Band WHERE owner = %s", param.ID)
        ownsList = [ ]
        for o in owns:
            ownsList.append(o.name)
#        bandsAndProjects = db.query("SELECT bop.bandName, p.name FROM Band b, Project p, BandOwnsProjects bop WHERE b.owner = %s AND bop.bandName = b.name AND bop.ID = p.ID", param.ID)
        bandsAndProjects = db.query("SELECT bop.bandName, p.name FROM MemberOf mo, Project p, BandOwnsProjects bop WHERE mo.email = %s AND bop.bandName = mo.bandName AND bop.ID = p.ID", param.email)
        mapping = dict()
        for item in bandsAndProjects:
            if mapping.has_key(item.bandName):
                temp = mapping[item.bandName]
                newlist = temp.append(item.name)
#                mapping[item.bandName] = newlist (this not needed, still doesnt make sense for me)
            else:
                mapping[item.bandName] = [item.name]
        self.render("profilepage.html", param = param, bands=bands, ownsList=ownsList, mapping=mapping)

    def post(self):
        user = self.get_current_user()
        bandName = self.get_argument("bandName")
        people = self.get_argument("people")
        registered = db.query("SELECT email FROM User")
        isBandExist = db.query("SELECT * FROM Band WHERE name = %s", bandName)
        peopleAdded = ""
        peopleFailed = ""
        registeredList = [ ] #put the queried result in a list
        for u in registered:
            registeredList.append(u.email)
        if isBandExist:
            self.write("band already exists")
            return None
        else:
            db.execute("INSERT INTO Band (name, owner) VALUES(%s, %s)", bandName, user.ID)
            db.execute("INSERT INTO MemberOf (email, bandName) VALUES(%s, %s)", user.email, bandName)
        if (people != "empty"):
            members = people.split(', ')
            for member in members:
                if (member in registeredList):
                    db.execute("INSERT INTO MemberOf (email, bandName) VALUES (%s, %s)", member, bandName)
                    peopleAdded += " "+member
                else:
                    peopleFailed += " "+member
            if not peopleFailed == "":
                self.write("People added are "+ peopleAdded+"\n"+"This user(s) does not exist "+peopleFailed)
                return None
            else:
                self.write("People added are "+ peopleAdded)
                return None
#        self.redirect("/profile", permanent=False)

class BandDeleteHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        bandName = self.get_argument("bandName")
        db.execute("DELETE FROM Band WHERE name=%s", bandName)
        self.redirect("/profile", permanent=False)

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
        elif action == "save":
            session.save(self.bandname, self.projname)
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
        for username in self.proj._Project__currentUsersMap:
            print("telling about: " + username)
            self.write_message("addUser: " + username + "," + self.proj._Project__currentUsersMap[username])

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


# Have one global connection to the blog DB across all handlers
db = tornado.database.Connection(host=options.mysql_host, database=options.mysql_database,
                                 user=options.mysql_user, password=options.mysql_password)
session = SessionManager(db)

main()

