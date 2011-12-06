-- This is the schema for collaboratory project for cs169 fa11.
-- Unless otherwise noted, all "lists" are basically comma separated values.

-- To create the database:
--   CREATE DATABASE collaboratory;
--   GRANT ALL PRIVILEGES ON collaboratory.* TO 'collaboratory'@'localhost' IDENTIFIED BY 'collaboratory';
--
-- To reload the tables:
--   mysql --user=collaboratory --password=welcome --database=collaboratory < schema.sql

SET SESSION storage_engine = "InnoDB";
SET SESSION time_zone = "+0:00";
ALTER DATABASE CHARACTER SET "utf8";


drop database collaboratory;
create database collaboratory;
use collaboratory;


DROP TABLE IF EXISTS User;
CREATE TABLE User (
	ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	email VARCHAR(100) NOT NULL UNIQUE,
	name VARCHAR(100) NOT NULL,
	password VARBINARY(100) NOT NULL /*we will use sha1 encryption*/
	-- bands VARCHAR(500), /* a list of band names*/
	-- projects VARCHAR(500), /*we put the id of the project here*/
	-- files VARCHAR(1000) /* a list of filenames.*/
);

DROP TABLE IF EXISTS Band;
CREATE TABLE Band (
	name VARCHAR(100) NOT NULL PRIMARY KEY,
	-- members VARCHAR(100) NOT NULL, /*we put the id of the user here separated by comma*/
	-- files VARCHAR(1000) NOT NULL, /* a list of filenames.*/
	owner INT NOT NULL /*the id of the user*/
);

DROP TABLE IF EXISTS Project;
CREATE TABLE Project (
	ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	files VARCHAR(1000) /* a list of filenames, comma separated.*/
);

DROP TABLE IF EXISTS Track;
CREATE TABLE Track (
	globalID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
	projectID INT NOT NULL,
	name VARCHAR(100) NOT NULL,
	clips VARCHAR(1000) NOT NULL, /* a list of clip info strings.  [position (in seconds)] [libraryClipName] [startTime] [endTime],[[etc.]]*/
	volume INT, /*the id of the user*/
	panning INT, /*the id of the user*/
	FOREIGN KEY (projectID)
		REFERENCES Project(ID)
		ON DELETE CASCADE
);

DROP TABLE IF EXISTS BandOwnsProjects;
CREATE TABLE BandOwnsProjects (
	bandName VARCHAR(100) NOT NULL,
	ID INT NOT NULL,
	FOREIGN KEY (bandName)
		REFERENCES Band(name)
		ON DELETE CASCADE,
	FOREIGN KEY (ID)
		REFERENCES Project(ID)
		ON DELETE CASCADE
);

DROP TABLE IF EXISTS UserOwnsProjects;
CREATE TABLE UserOwnsProjects (
	email VARCHAR(100) NOT NULL,
	ID INT NOT NULL,
	FOREIGN KEY (email)
		REFERENCES User(email)
		ON DELETE CASCADE,
	FOREIGN KEY (ID)
		REFERENCES Project(ID)
		ON DELETE CASCADE
);

DROP TABLE IF EXISTS MemberOf;
CREATE TABLE MemberOf (
	email VARCHAR(100) NOT NULL,
	bandName VARCHAR(100) NOT NULL,
	FOREIGN KEY (email)
		REFERENCES User(email)
		ON DELETE CASCADE,
	FOREIGN KEY (bandName)
		REFERENCES Band(name)
		ON DELETE CASCADE
);

CREATE INDEX TrackIndex
	ON Track(projectID);







/* Insert a test project */
INSERT INTO Band
	VALUES ("band", "admin@test.com");
	
INSERT INTO User (email, name, password)
	VALUES("admin@test.com", "admin", "admin");
	
INSERT INTO User (email, name, password)
	VALUES("member1@test.com", "member1", "member1");
	
INSERT INTO MemberOf
	VALUES ("admin@test.com", "band");
	
INSERT INTO MemberOf
	VALUES ("member1@test.com", "band");

INSERT INTO Project (name, files)
	VALUES ("proj", "woman.wav");

INSERT INTO BandOwnsProjects
	VALUES ("band", 1 );
	
INSERT INTO UserOwnsProjects
	VALUES ("admin@test.com", 1);

INSERT INTO UserOwnsProjects
	VALUES ("member1@test.com", 1);

INSERT INTO Track (projectID, name, clips, volume, panning)
	VALUES (1, "track 1", "0 woman.wav 0 5", 100, 50);
	
	
/* Insert a test user */
