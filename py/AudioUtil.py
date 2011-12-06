'''
Created on Nov 6, 2011

@author: Justin
'''

import os.path
import wave
import logging

def getWaveFileDuration(path):
    '''
    Returns duration of a wave file in seconds, or 0 if the file is not existent or not a wave file.
    '''
    if(os.path.exists(path) and path.endswith(".wav")):
        waveFile = wave.open(path, "r")
        #frames = file.getnframes()
        #rate = file.getframerate()
        duration = waveFile.getnframes() / float(waveFile.getframerate())
        logging.info("length of " + path + " is " + str(duration))
        return duration
    else:
        return 0