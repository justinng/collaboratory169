'''
Created on Oct 26, 2011

@author: Justin
'''
import unittest
from ProjectInstance import *


class Test(unittest.TestCase):


    def setUp(self):
        self.sessionManager1 = SessionManager()
        self.sessionManager2 = SessionManager()

    def tearDown(self):
        pass


    def test_sessionmanager_singleton(self):
        self.assertIs(self.sessionManager1, self.sessionManager2, "SessionManager singleton-ness failure.")
        
    def test_loading_projects(self):
        self.sessionManager1.load("band1", "proj1")
        self.sessionManager1.load("band1", "proj2")
        projectMapSize = len( self.sessionManager1.getBand("band1")._BandManager__projectMap )
        self.assertEqual(projectMapSize, 2, "BandManager's __projectMap not responding to load commands.")
        
        self.sessionManager1.unload("band1", "proj1")
        self.sessionManager1.unload("band1", "proj2")
        self.assertFalse( self.sessionManager1.getBand("band1") , "BandManager's __projectMap not responding to unload commands.")
        
    def test_addClip(self):
        project = self.sessionManager1.load("band1", "proj1")
        project.newLibraryClip("/", "Dummy LibraryClip")
        project.newTrack("track1")
        project.addClipToTrack("track1", 0, "Dummy LibraryClip", 0, 1)
        track1ClipCount = len( project._Project__trackMap["track1"]._Track__clipsSet )
        self.assertEqual(track1ClipCount, 1, "addClipToTrack failure.")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()