'''
Created on Nov 6, 2011

@author: Justin
'''

import os.path
import wave

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
from pylab import *


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
    
def renderWaveform(filepath, filename):
    
    COLOR = "#0000FF"
    INCHES_PER_SECOND = 0.5
    
    soundFile = wave.open(filepath,'r')
    soundInfo = soundFile.readframes(-1)
    soundInfo = fromstring(soundInfo, 'Int16')
    
    fig = figure(figsize = (soundFile.getnframes()/float(soundFile.getframerate()) * INCHES_PER_SECOND, 1), frameon = False)
   
    ax = fig.add_axes([0,0,1,1], frameon = False)
    plot(soundInfo, color = COLOR, antialiased = True)
    
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_view_interval(0, len(soundInfo), ignore=True)
    
    savefig( os.path.join( os.path.split(filepath)[0], filename.split(".")[0] ))
    logging.info("Wrote waveform png for: " + filename)
    soundFile.close()