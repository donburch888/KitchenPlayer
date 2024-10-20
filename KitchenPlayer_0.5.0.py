#!/usr/bin/env python3
# 
#########################################################################
#									#
#		Don's simple Kitchen music Player			#
#									#
#########################################################################
#
# Purpose: Most music players assume audiophile users who will select
#       each track or album to play ... 
#       However I just want to turn on background music like a radio, but
#       without adverts or annoying DJs. 
#
# Target Hardware: A Raspberry Pi with audio HAT and 7" touch screen.
#	The model of RasPi, audio device or screen can be altered. 
#
# Scope: I have 17000 music tracks and several playlists already defined; 
#	it would be pontless not to use them. 
#	KitchenPlayer ONLY provides a simple User Interface for MPD, 
#	like a car radio, where user presses a button to start a 
#	pre-defined playlist or streaming radio station. 
#
#	Kitchen Player sends commands to MPD, which does all the heavy lifting ... 
#	maintaining database of tracks, playlists and doing the playing. 
#
#	This is easy ... except that we would like to show what song 
#	is currently playing ... which requires us to keep checking MPD. 
#	To reduce the processing load of constantly checking MPD, 
#	KitchenPlayer determines the time for each track and counts 
#	seconds until the track should have finished.
#
#	A Windows-style .ini file is used for most controllable parameters.
#
# 	Curating the music and other configuration is assumed to be
#	done independently from other PCs. 
#
#	ver 0.4.0 After a bit of a re-think, I change the programs method.
#	(a) There should be one function which constantly monitors what
#		MPD is doing, and updates the 'Now Playing' display 
#	(b) Buttons modify MPD and parameters
#	
#
# History:
# 	based on mmc4w.py - 2024 by Gregory A. Sanders (dr.gerg@drgerg.com)
# 	Minimal MPD Client for Windows - basic set of controls for an MPD server.
#       	mmc4w version "v2.1.0"
#
#       Greg designed mmc4w to take up minimal screen space on his desktop PC.
#	My use case is almost opposite - piority is ease-of-use for my
#	non-technical partner to use while cooking in the kitchen. 
#       Consequently I have made major changes to the User Interface 
#       and stripped out a lot of functionality.
#
# 	Massive thanks to Gregory saving me from starting from scratch 
#       with the python code for interacting with TKinter and MPD. 
#
# Major changes:
#	I have added streaming Radio Stations, which have several 
#	significant differences from playlists:
#	(1) Only one line is in the playlist file, which contains 
#	    the URL of the streaming radio station.
#	(2) There is no track duration, and so we need an alternative 
#	    to using a timer.
#	(3) There is no album artwork in the folder containing the music, 
#	    so we need a different mechanism to display station's artwork.  
#
# Prerequisites:
# 	KitchenPlayer.py uses the python-musicpd, TKInter and PIL libraries; 
#	which are assumed to already be installed on the RasPi.
#
#
#########################################################################
#									#
#		version history						#
#									#
#########################################################################
programName  = "KitchenPlayer"
programTitle = "Don's Kitchen Music Player"
version = "0.5.0"
# 0.1.0 Sept 2024 - Initial conversion from mmc4w 
#		  - cut out all the threading and simplify timing
# 0.2.0 Oct 2024  - continued conversion.  Remove all pop-ip windows,
#		     menus and artwork. Ensure countdown working correctly,
#		     especially when pausing or changing playlist.
#		  - Add radio stations, including countdown radio.
# 0.3.0 Oct 2024  - First version on Github. Add [Remove] function, tidy
#		     variable names
#		  - wrap MPD Client calls to add auto reconnect if needed. 
#		     Change client.<command>() calls to MPD('<command>'[,argument]) 
#		     You can still call client.status() directly in tight
#		     loops where program won't have time to disconnect.
# 0.4.0 Oct 2024  - restructure to have one process monitoring the music 
#		     player; with the [Play], [Pause] and radio buttons
#		     simply directing what should be being played. 
#		  - adjust a single radio station playlist.m3u file
#		     as required from the definitions 
#		  - Ini file create single list of button definitions, 
#		     to indicate whether playlist or radio; and change
#		     code to use this rather than playlist name.
#		  - if radio station playing, hide [Prev], [Next] buttons
#		  - logger.debug for full details and new each session; 
#		     logger.info to grow constantly, for errors & events
#		     which may need to be referred to later (eg [Remove].
#		  - focus on checking what MPD is up to, rather than
#		     relying on in-memory status variables. Particularly
#		     important when another app (eg HA Music Assistant)
#		     can also be controlling MPD
#
# 0.5.0 Oct 2024  - add artwork. MPD's readpicture function looks for 
#		     artwork embedded in the music track, and albumart 
#		     searches the directory the file resides in for a 
#		     a file called cover.png, cover.jpg, or cover.webp.
#		     My music has artwork in folder.jpg, so have to add 
#		     checks for that. 
#		 - adjust screen formatting to fill entire 7" screen.
#		    Space for a couple more radio stations
#		 - 

# Initial Volume on buttons

# had a song which showed NO DETAILS.  Why? an .avi file without ID3 tags
# now_playing  Playlist=nzmusic, Status=play, 
#	currSong=file: NZ Music/Darren Hanlon/A To Z (Live Brisbane 2007).avi.
# song changed to currSong={'file': 'NZ Music/Darren Hanlon/A To Z (Live Brisbane 2007).avi', 
#	'last-modified': '2009-11-07T00:41:42Z', 'format': '48000:f:2', 'time': '224', 
#	'duration': '224.480', 'pos': '71', 'id': '25194'}, playlistType[nzmusic]=playlist.
#
# added def getFilenameDetail(filename):

#
# still to do:	- 
#		- pop-up to alter the toggle switches
#		- [Select] button to select artist or album within current playlist
#		- add parameters for number of rows and columns of radio buttons,
#			ie remove the row and col from the ini file, and
#			instead allocate the buttons in order for row=5 to 10, 
#			for col=0 to 2
#

import tkinter as tk		# requires TKinter
from tkinter import messagebox
from tkinter import simpledialog
from tkinter.font import Font
from PIL import ImageTk, Image	# requires PIL libary
import musicpd			# requires python-musicpd 
				# refer: https://kaliko.gitlab.io/python-musicpd/
import datetime
from time import sleep
import sys
from configparser import ConfigParser
import os
import urllib.request
import io
import time
import logging
from collections import OrderedDict
from pathlib import Path

#if sys.platform != "win32":
#    import subprocess
#else:
#    # from win32api import GetSystemMetrics
#    import ctypes
#    ctypes.windll.shcore.SetProcessDpiAwareness(0)
#    ctypes.windll.user32.SetProcessDPIAware()



#########################################################################
#									#
#	Constants definitions						#
#									#
#########################################################################

global confparse, currStatus, currSong, currPlaylist, playlistType

# colours used for buttons
colrButton = "grey90"			# default button colour
colrDisabled = "white"
colrPaused = "green1"			# play/pause when paused
colrSelected = "skyblue1"		# the active radio button
colrVolume = {		# volume button definitions
    # key:  Vol+ label, bg color, fg color,	 Vol- label, bg color, fg color
    100: ['100','gray13','white',	 'Vol -','gray90','black'],
    95:  [ '95','gray12','white',	 'Vol -','gray90','black'],
    90:  [ '90','AntiqueWhite4','white', 'Vol -','gray90','black'],
    85:  [ '85','AntiqueWhite4','white', 'Vol -','gray90','black'],
    80:  [ '80','AntiqueWhite3','black', 'Vol -','gray90','black'],
    75:  [ '75','AntiqueWhite3','black', 'Vol -','gray90','black'],
    70:  [ '70','AntiqueWhite2','black', 'Vol -','gray90','black'],
    65:  [ '65','AntiqueWhite2','black', 'Vol -','gray90','black'],
    60:  [ '60','AntiqueWhite1','black', 'Vol -','gray90','black'],
    55:  [ '55','AntiqueWhite1','black', 'Vol -','gray90','black'],
    50:  ['Vol +','gray90','black',      'Vol -','gray90','black'],
    45:  ['Vol +','gray90','black',     '45','CadetBlue1','black'],
    40:  ['Vol +','gray90','black',     '40','CadetBlue1','black'],
    35:  ['Vol +','gray90','black',     '35','turquoise1','black'],
    30:  ['Vol +','gray90','black',     '30','turquoise1','black'],
    25:  ['Vol +','gray90','black',     '25','turquoise2','black'],
    20:  ['Vol +','gray90','black',     '20','turquoise2','black'],
    15:  ['Vol +','gray90','black',     '15','turquoise3','black'],
    10:  ['Vol +','gray90','black',     '10','turquoise3','black'],
    5:   ['Vol +','gray90','black',      '5','turquoise4','white'],
    0:   ['Vol +','gray90','black',      '0','turquoise4','white']
}


#########################################################################
#									#
#	get initial Configuration from KitchenPlayer.ini		#
#									#
#########################################################################
path_to_dat = Path(__file__).parent
iniFilename = path_to_dat / (programName +".ini")
workDir = os.path.expanduser("~")
if sys.platform == "win32": slash = "\\"
else:                       slash = "/"
#print ("mmc4wIni is {}, iniFilename={}, workDir={}.".format(mmc4wIni,iniFilename,workDir) )

# confparse is for general use for normal text strings.
# for example, confparse.get('serverstats','playlists') returns the string:
#	Raffaellas,radio-Amore_SoloMusica,Albums,Oldies,Opera,default,
confparse = ConfigParser()	# current value of mmc4w.ini file as a dict
try:
    confparse.read(iniFilename)
except:
    endWithError("No configuration file {}.".format(iniFilename) )

# cp is for use where lists are involved.
# for example cp.getlist('serverstats','playlists') returns the list:
#	['Raffaellas', 'radio-Amore_SoloMusica', 'Albums', 'Oldies', 'Opera', 'default', '']
cp = ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
cp.read(iniFilename)

if confparse.get('basic','installation') == "":
    confparse.set('basic','installation',str(path_to_dat))
if confparse.get('basic','sysplatform') == "":
    confparse.set('basic','sysplatform',sys.platform)

#
# start the logger
#
logLevel = confparse.get('program','loglevel').upper()
logFilename = path_to_dat / (programName +".log")

if logLevel == 'OFF':
    logLevel = 'WARNING'

#if logLevel == "INFO":
# change- INFO should build a list of errors for later checking (Removed tracks),
# but DEBUG should be for details of the current session

if logLevel == 'DEBUG':
    os.remove(path_to_dat / (programName +"_DEBUG.log") )
    logging.basicConfig(
        filename=path_to_dat / (programName +"_DEBUG.log"),
        format="%(asctime)s - %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
        level=logging.DEBUG,
    )
elif logLevel == 'INFO':
    logging.basicConfig(
        filename=path_to_dat / logFilename,
        format="%(asctime)s - %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
        level=logging.INFO,
    )
else: 		# anything else defaults to 'WARNING':
    logging.basicConfig(
        filename=path_to_dat / logFilename,
        format="%(asctime)s - %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
        level=logging.WARNING,
    )
logger = logging.getLogger(__name__)
logger.debug(" ")
logger.debug(" v v v v v v v v v  NEW SESSION  v v v v v v v v ")
logger.info("    -----======<<<<  STARTING UP  >>>>======-----")
#logger.debug("D0) sys.platform is {}".format(sys.platform))

wglst = confparse.get("mainwindow","maingeo").split(',')

#
# get MPD server details
#
#serverlist = confparse.get('basic','serverlist')
serverip   = confparse.get('serverstats', 'lastsrvr')
serverport = confparse.get('basic','serverport')
MPD_music_directory = confparse.get('basic','music_directory')
MPD_playlist_directory = confparse.get('basic','playlist_directory')

#logger.debug("don1 confparse basic returns  serverlist="+ serverlist +", serverip="+ serverip +"  serverport="+ serverport )
if serverip == "":
    proceed = messagebox.askokcancel("Edit Config File","serverip required in mmc4w.ini.")
    if proceed == True:
        if sys.platform == "win32":
            os.startfile(iniFilename)
        else:
            subprocess.run(["xdg-open", iniFilename])
        sys.exit()

if confparse.get('serverstats','lastport') != "":
    serverport = confparse.get('serverstats','lastport')
else:
    confparse.set('serverstats','lastport',serverport)

if version != confparse.get('program','version'):
    #### should this be an error because program and config file out of sync ???
    confparse.set('program','version',version )

# update all the .ini configuration parameters
with open(iniFilename, 'w') as SLcnf:
     confparse.write(SLcnf)



#########################################################################
#									#
#	Connect to MPD and LOAD INITIAL VALUES				#
#									#
#########################################################################
client = musicpd.MPDClient()	# create MPD client object
client.timeout = None		# network timeout in seconds (floats allowed), default: None
client.idletimeout = None	# timeout for fetching the result of the idle command is handled seperately, default: None

#
#	make sure the MPD server is operational,
# 	providing a helful error message if not.
#
try:
    logger.debug("D1| Initial connect to MPD at {} on port {}".format(serverip,serverport))
    client.connect(serverip, int(serverport))
except  (ValueError, musicpd.ConnectionError, ConnectionRefusedError,ConnectionAbortedError) as err2var:
    if err2var == 'Already connected':
        pass
    elif 'WinError' in str(err2var) or 'Not connected' in str(err2var):
        endWithError("The server you selected is not responding. Edit mmc4w.ini to ensure the 'lastsrvr' IP address is for a running server.")
    else:
        logger.debug("D1| Second level errvar: {}".format(err2var))
        endWithError("The server you selected is not responding.\nEdit mmc4w.ini to ensure the 'lastsrvr' IP address is for a running server.")
else:
    logger.debug("D1| Connect to MPD client successful")


#########################################################################
#									#
#	initialise a few main variables					#
#									#
#########################################################################
#
#	they will be assigned values later, but must exist first
#
		# currStatus  is current value of dict client.status()
currStatus = dict()		# define current MPD state as a dict
		# currSong  is current value of dict client.currentsong()
currSong = dict()		# define current song as a dict
currPlaylist = ''



#########################################################################
#									#
#			System functions				#
#									#
#########################################################################

def endWithError(msg):
    messagebox.showinfo("UhOh",msg)
    sys.exit()
    window.destroy()



def updateIni(section, key, value):
    confparse.set(section,key,value)
    with open(iniFilename, 'w') as SLcnf:
        confparse.write(SLcnf)
    logger.debug("ini file  section [{}] updated with {} = {}".format(section, key, value) )



def exit():
    global client, window
    logger.debug("EXIT() Connections closed. Playback stopped. Quitting.")
    MPD('stop')				#  client.stop()
    sleep(2)
    currStatus = client.status()
#    logger.debug("after 1st attempt, client.status()={}".format(client.status()) )

#    sys.exit()				# sys.exit works for single thread, 
					# but tkinter needs the main window destroyed
    window.destroy()				# close tkinter window, exiting the program
    logger.debug("EXIT() ended. .")



def fileExists( filename ):
    # return True if file exists, otherwise False
    try:
        f = open(filename, 'r')		# open to read
        # file exists, so dispplay it
        f.close()			# don't leave masses of open files
        return True
    except:
        return False



#########################################################################
#									#
#		Wrapper for calling the MPD server			#
#									#
#########################################################################
#
#	If the connection has dropped, try to reconnect it
#
def MPD(mpdFunction,*arg1):
    global serverip,serverport
    if len(arg1) > 0 :	arg1 = arg1[0]		# only one optional argument
    logger.debug("MPD({},{}) called".format(mpdFunction,arg1) )
    try:
	# status functions (in anticipated order of frequency, for efficiency)
        if   mpdFunction == 'connect':      return client.connect(serverip,serverport)
        elif mpdFunction == 'status':       return client.status()
        elif mpdFunction == 'currentsong':  return client.currentsong()
        elif mpdFunction == 'play':         return client.play()
        elif mpdFunction == 'pause':        return client.pause()
        elif mpdFunction == 'next':         return client.next()
        elif mpdFunction == 'previous':     return client.previous()
        elif mpdFunction == 'volume':       return client.volume(arg1)
        elif mpdFunction == 'load':         return client.load(arg1)
        elif mpdFunction == 'add':          return client.add(arg1)
        elif mpdFunction == 'clear':        return client.clear()
        elif mpdFunction == 'clearerror':   return client.clearerror()
        elif mpdFunction == 'stop':         return client.stop()
        elif mpdFunction == 'setvol':       return client.setvol(arg1)
        elif mpdFunction == 'listplaylists': return client.listplaylists()
        elif mpdFunction == 'deleteid':     return client.deleteid(arg1)
        elif mpdFunction == 'save':         return client.save(arg1)
        elif mpdFunction == 'ping':         return client.ping()
        elif mpdFunction == 'random':       return client.random(arg1)
        elif mpdFunction == 'repeat':       return client.repeat(arg1)
        elif mpdFunction == 'consume':      return client.consume(arg1)
        elif mpdFunction == 'single':       return client.single(arg1)
        else:
            logger.info("MPD - unknown function "+ mpdFunction +" requested.")

    except (musicpd.ConnectionError, ConnectionRefusedError,ConnectionAbortedError, musicpd.ProtocolError) as errvar:
        logger.debug("MPD({},{}) 1st exception errvar={}".format(mpdFunction,arg1,errvar))
        if errvar == 'Already connected':
            pass
        else:
            #
            # assume connection to MPD server has dropped, so reconnect and try again
            #
            try:
                errvar = ''
                logger.debug("MPD  Try to reconnect to {} on port {}".format(serverip,serverport))
                client.connect(serverip, int(serverport))
            except  (ValueError, musicpd.ConnectionError, ConnectionRefusedError,ConnectionAbortedError) as errvar:
                logger.debug("MPD({},{}) 2nd exception errvar={}".format(mpdFunction,arg1,errvar))
                if errvar == 'Already connected':
                    pass
                elif 'WinError' in str(errvar) or 'Not connected' in str(errvar):
                    endWithError("The server you selected has stopped responding. ")
                else:
                    logger.debug("MPD  ***** MPD() second level error {} *****".format(errvar) ) 
                    endWithError("The server you selected is not responding.")
        # Repeat the long if statement
        if   mpdFunction == 'connect':      return client.connect(serverip,serverport)
        elif mpdFunction == 'status':       return client.status()
        elif mpdFunction == 'currentsong':  return client.currentsong()
        elif mpdFunction == 'play':         return client.play()
        elif mpdFunction == 'pause':        return client.pause()
        elif mpdFunction == 'next':         return client.next()
        elif mpdFunction == 'previous':     return client.previous()
        elif mpdFunction == 'volume':       return client.volume(arg1)
        elif mpdFunction == 'load':         return client.load(arg1)
        elif mpdFunction == 'add':          return client.add(arg1)
        elif mpdFunction == 'stop':         return client.stop()
        elif mpdFunction == 'clear':        return client.clear()
        elif mpdFunction == 'clearerror':   return client.clearerror()
        elif mpdFunction == 'setvol':       return client.setvol(arg1)
        elif mpdFunction == 'listplaylists': return client.listplaylists()
        elif mpdFunction == 'deleteid':     return client.deleteid(arg1)
        elif mpdFunction == 'save':         return client.save(arg1)
        elif mpdFunction == 'ping':         return client.ping()
        elif mpdFunction == 'random':       return client.random(arg1)
        elif mpdFunction == 'repeat':       return client.repeat(arg1)
        elif mpdFunction == 'consume':      return client.consume(arg1)
        elif mpdFunction == 'single':       return client.single(arg1)
        else:
            logger.info("unknown function "+ mpdFunction +" requested.")

    # if we got here connection is OK - otherwise we already did an endWithError !
    logger.debug("MPD returns {}.")		#.format(retVal) )
    return 



#########################################################################
#									#
#	WINdow GEOmetrey translATOR
#									#
#########################################################################
#
# wingeoxlator(geostring,None,'') brings in a tkinter geometry() string and outputs a list that
#   configparser can deal with.
#
# wingeoxlator('',ValuesListObject,'') takes in a list of values and
#   output them in the proper string format to use in a tk.geometry() call.
#
# wingeoxlator('',None,ValuesListObject) converts a list object back into a 
#   configparser comma-delimited string.
#
def wingeoxlator(geostring,geovals,geolist):
        logger.debug("called wingeoxlator({},{},{})".format(geostring,geovals,geolist) )
        geostr = ''
        cnflist = []
        outstring = ''
        if geostring != '': # Convert tk.geometry() string to configparser string entry.
            cnflist = geostring.replace('x',' ')
            cnflist = cnflist.replace('+',' ')
            cnflist = cnflist.split()
            confstr = str("{},{},{},{}".format(cnflist[0],cnflist[1],cnflist[2],cnflist[3]))
            return confstr
        if geovals != None: # Convert values list object to tk.geometry() string.
            outstring = geovals[0] + 'x' + geovals[1] + '+' + geovals[2] + '+' + geovals[3]
            return outstring
        if geolist != None: # Convert values list object to configparser string entry.
            geostr = str("{},{},{},{}".format(geolist[0],geolist[1],geolist[2],geolist[3]))
            return geostr





#########################################################################
#									#
#		Window Button actions					#
#									#
#########################################################################

#
#	Play / Pause button 
#
# One button is used to Play or Pause the music, with the button label 
# 	changing as appropriate.
#
# While MPD may have 3 states ('stop', 'play' or 'pause'), the button 
#	only has two.
# It is possible for MPD to be controlled from another client, leaving 
#	this player out of sync with MPD. 
# Thus it is necessary to constantly check client.status
#
def btnPause():			# The user has pressed the Pause button
    logger.debug("btnPause() called ")	#with currStatus['state']={}.".format(currStatus['state']) )
    MPD('pause')			# client.pause()


def btnPlay():			# The user has pressed the Play button
#    logger.debug('btnPlay() called with currStatus={}.'.format(currStatus) )
    logger.debug("btnPlay() called ")	#with currStatus['state']={}.".format(currStatus['state']) )
    MPD('play')				# client.play()	# start MPD playing


def next():
    MPD('next')		# client.next()


def previous():
    MPD('previous')        # client.previous()


def volup():
#    global lastvol
    vol_int = int(lastvol) + 5
    if vol_int <= 100:
        client.setvol(vol_int)
        volbtncolor(vol_int)


def voldn():
#    global lastvol
    vol_int = int(lastvol) - 5
    if vol_int >= 0:
        client.setvol(vol_int)
#        vol_int = vol_int - 5
        volbtncolor(vol_int)


def plrandom(stat):
    if stat == 0:
#        plnotrandom()  # Set sequential playback mode.
        text1['bg']='navy'
        text1['fg']='white'
    else:
#        plrandom()     # Set random playback mode.
        text1['bg']='white'
        text1['fg']='black'


def togl(key):
    stat = toggleStatus[key]
    symb = toggleSymbols[key]
    if stat == 0:
        stat = 1
        symb = symb.upper()
        msg = key + ' is set to ON.'
    else:
        stat = 0
        symb = symb.lower()
        msg = key + ' is set to OFF.'
    if key == 'random': 
        client.random(stat)
        plrandom(stat)
    if key == 'repeat': client.repeat(stat)
    if key == 'consume': client.consume(stat)
    if key == 'single': client.single(stat)
    logger.debug("togl({}) toggleStatus={}, toggleSymbols={},  msg={}".format(key,toggleStatus,toggleSymbols,msg) )
    displaytrack(msg,'')
    toggleStatus[key] = stat
    toggleSymbols[key] = symb


def toglsingle():
    togl('single')



#########################################################################
#									#
#	SELECT an album, or Artist from the current playlist		#
#									#
#########################################################################
#
def select():
    logger.debug("select() called - add code later !")
#button_select = tk.Button(main_frame, width=9, bg='gray90', text="Select", font=nnFont, command=select)



#########################################################################
#									#
#	REMOVE the currently playing track from the playlist 		#
#									#
#########################################################################
# I have tried to add variety to my music collection, and this has 
# 	included some tracks I and my partner are not keen on. 
# Since the KitchenPlayer is working off a copy of my complete music 
#	collection, it seems easiest to simply delete any offending 
#	track, and maybe review the choices later.
def remove():
    global client, currSong, currStatus
    if playlistType[currPlaylist] == 'stream':
        messagebox.showinfo("Cannot remove a song from a radio station")
        return

    logger.debug("remove() currPlaylist={}, currSong={}, currStatus={}.".format(currPlaylist,currSong,currStatus) )
    # determine which is the offending song
    songID = currStatus['songid']
    if currSong['id'] != songID:
        messagebox.showinfo("ERROR - SONG IDs DO NOT MATCH", f" currSong['id']={currSong['id']}, currStatus['songid']={songID}" )
    filename = currSong['file']
    # confirm it is to be removed  
    if messagebox.askokcancel("Are you sure ?",f"REMOVE {currSong['title']}" ):
        # remove from the playlist
        client.deleteid(songID)
        logger.warning('##### LOG: remove {} by {} from playlist {}'.format(currSong['title'],currSong['artist'],currPlaylist) )
        try:
#            client.save(currPlaylist,'replace')	# replace playlist file with modified version
# MPD docs show save <playlist> having a parameter for create or replace, 
# but python-musicpd does not allow a parameter
# Think maybe i need to delete and then crease
            client.rm(currPlaylist)		# replace playlist file with modified version
            client.save(currPlaylist)		# replace playlist file with modified version
        except Exception as e:
            logger.debug(f"client.save exception {e}")

        # delete the file from the music directory
        filename = MPD_music_directory + slash + filename
        try:
            temp = os.path.isfile( filename)
        except Exception as e:
            logger.debug(f"os.path.isfile()  exception {e}")
        if temp:
#            logger.debug('remove    os.remove({})'.format(  filename) )
            try:
                os.remove(path_to_dat / filename)
                # log the file which was deleted (in case it should be reinstated manually later)
                logger.warning('##### LOG: removed file {}'.format(filename) )
            except Exception as e:
                logger.debug(f"os.remove(filename) exception {e}")
        else:
            logger.debug(f"   ## NOT isfile")


#########################################################################
#									#
#	SWITCHES to display and optionally change the toggles		#
#									#
#########################################################################
#
def switches():
    global toggleSymbols
    logger.debug("switches() called - add code later !")
#
# pop-up window containing settings for :
# Toggle Random", command=toglrandom)
# Toggle Repeat", command=toglrepeat)
# Toggle Consume", command=toglconsume)
# Toggle Single", command=toglsingle)

    # and update the flags and switches
    msg = "{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'])
#    logger.debug("{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'],currPlaylist) )
    button_switches.configure(text=msg,bg='gray90') 



def btn_disabled():
    # button has been disabled, so do nothing
    return



#########################################################################
#									#
#		Display artwork						#
#									#
#########################################################################

#
# DEFINE THE ART WINDOW
#
# aart = artWindow(1)  ## artWindow now returns aart ready for use.
# artWindow prepares the image, 'configs' the Label and returns image as well.

def artWindow(thisimage):
#    logger.debug(f"artWindow({thisimage}) called .")
    if thisimage == '':
        thisimage = path_to_dat / "ico/mmc4w.png"	# use default image
    aart = Image.open( thisimage ) 	# the URL of the image for the radio station
    aart = aart.resize((artwinilist[0],artwinilist[1]))
    aart = ImageTk.PhotoImage(aart)
    aart.image = aart  # required for some reason
    return aart


def artWindowRadio(thisimage):
#    logger.debug(f"artWindowRadio({thisimage}) called  ")
    if thisimage == '':
        thisimage = path_to_dat / "ico/mmc4w.png"	# use default image

    aart = display_image_from_url(thisimage)
    aart = aart.resize((artwinilist[0],artwinilist[1]))
    aart = ImageTk.PhotoImage(aart)
    aart.image = aart  # required for some reason
    return aart


# Define function to fetch images from url and exception handling
def display_image_from_url(url):
    aart = ''
    try:
        with urllib.request.urlopen(url) as u:
            raw_data = u.read()
    except Exception as e:
        logger.debug(f"Error '{e}' fetching image: {url}")
        return

    try:
        aart = Image.open(io.BytesIO(raw_data))
    except Exception as e:
        logger.debug(f"Error '{e}' opening image: {url}")
        return

    return aart



def getaartpic(currSong):		# get the album artwork for currSong
#    global aartvar, currSong
    #
    # This function has 3 phases:
    #	1) use MPD readpicture to check for an image embedded in the song file 
    #	2) use MPD albumart to check the directory for cover.png, cover.jpg, or cover.webp
    #	3) look in directory for folder.jpg, and in parent folder for folder.jpg
    # In the first 2 cases, the image is copied to cover.png for display
    #
    logger.debug(f"getaartpic() called.  currSong['file']={currSong['file']}")
    eadict = {}
    fadict = {}
    #
    # 1) readpicture looks for a picture embedded in the song file
    #
#    eadict = client.readpicture(cs['file'],0)
    eadict = client.readpicture(currSong['file'],0)
    if len(eadict) > 0:
        size = int(eadict['size'])
        done = int(eadict['binary'])
        logger.debug(f"readpicture found.  size={size}, done={done}.")
        with open(path_to_dat / "cover.png", 'wb') as cover:
            cover.write(eadict['data'])
            while size > done:
                eadict = client.readpicture(currSong['file'],done)
                done += int(eadict['binary'])
                cover.write(eadict['data'])
        logger.debug(f"D6| Wrote {done} bytes to cover.png.  len(eadict) is: {len(eadict)}.")
#        aartvar = path_to_dat / "cover.png"
        return path_to_dat / "cover.png"
    else:
        #
        # 2) # albumart searches the directory the file resides in 
	#	for a file called cover.png, cover.jpg, or cover.webp
        #
        try:
            fadict = client.albumart(currSong['file'],0)
            logger.debug(f"albumart  len(fadict)={len(fadict)}.")
            # albumart did find the file
            if len(fadict) > 0:
                received = int(fadict.get('binary'))
                size = int(fadict.get('size'))
                logger.debug(f"albumart found.  size={size}, done={received}.")
                with open(path_to_dat / "cover.png", 'wb') as cover:
                    cover.write(fadict.get('data'))
                    while received < size:
                        fadict = client.albumart(currSong['file'], received)
                        cover.write(fadict.get('data'))
                        received += int(fadict.get('binary'))
                logger.debug(f"D6| Wrote {received} bytes to cover.png.  len(fadict) is: {len(fadict)}.")
#                aartvar = path_to_dat / "cover.png"
                return path_to_dat / "cover.png"
            else:
                logger.debug(f"albumart else   len(fadict)={len(fadict)}.  ")
#                aartvar = ''
                return ''
        except musicpd.CommandError:
            # nope, albumart throws an exception if it can't find the file
            #
            # 3) so lets try looking for folder.jpg
            #
            logger.debug(f"no embedded picture and no albumart.  try looking for folder.jpg")
            aartvar = ''
            tempSong = currSong['file']

            tempSong = parentFolder(tempSong)		# trim off the last part of filename
            aartvar = find_file( tempSong, "folder.jpg" )
            if aartvar == '':
                # try again in the parent folder
                tempSong = parentFolder(tempSong)	# trim off the last folder 
                aartvar = find_file( tempSong, "folder.jpg" )
            return aartvar
    # shouldn't get here, but log it just in case.
    logger.info(f"D6| Bottom of getaartpic().  aartvar={aartvar}, len(eadict)={len(eadict)}, len(fadict)={len(fadict)}.")


#
# return the parent folder of the given filename. 
#	if a path is given, return parent path
#
def parentFolder(filename):
    # find the folder by dropping the song filename
    # look for the last "/"  (or "\" if windows)
#    logger.debug(f"   parentFolder({filename}) called.")
    if filename.rfind(slash) > 0:
        # found the last slash, so return up to it
        return filename[:filename.rfind(slash)]
    else:
        return ''			# no "/" in the filename


def find_file(folder, filename):
    # does the MPD music filename exist in the supplied folder ?
    if folder != '':
        folder = folder + slash
    filename = MPD_music_directory + slash + folder + filename
    try:
        f = open(filename, 'r')		# open to read
        # file exists, so dispplay it
        logger.debug(f"   find_file found {filename}.")
        f.close()			# don't leave masses of open files
# or should use        temp = os.path.isfile( filename)
        return filename		# it exists, so dislay
    except:
        logger.debug(f"   find_file '{filename}' not found") 
        return ''


def getFilenameDetail(filename):
    # Can we work out what is missing from filename ?

    # return a list of keyword argument pairs in filename_parts
    temp = filename.rfind('.')
    filename_parts[ "extension"] = filename[temp:]	# after the last dot
    filename = filename[:temp]				# trim the extension off

    fnamFilename = filename.split(slash)		# separate at slashes
    numParts = len(fnamFilename)
    filename_parts[ "playlist"] = fnamFilename[0]			# first part

    if fnamPlaylist == "Singles":
        # in 'Singles' playlists the filename is Singles/<Artist> - <Title> . <Extension>
        if numParts > 2:
            # too many parts
            pass
    else:
        # assume filename comprises <playlist> / <Artist> / <Album> / <Title> . <Extension>
        #	where <Album> and/or <Artist> may be missing; or
        pass
    if fnamArtist != '':    filename_parts[ "artist"]    = fnamArtist
    if fnamAlbum != '':     filename_parts[ "album"]     = fnamAlbum
    if fnamTitle != '':     filename_parts[ "title"]     = fnamTitle
    return filename_parts

#########################################################################
#									#
#		SETUP MAIN TKinter WINDOWS DEFINITIONS			#
#									#
# This needs to be located in the code after the button action 		#
# functions have been defined, but before we try modifying the buttons	#
#									#
#########################################################################
#
#  THIS IS THE 'ROOT' WINDOW.  IT IS NAMED 'window' rather than 'root'.
window = tk.Tk()  # Create the root window with errors in console, invisible to Windows.
window.title(programTitle +" - v"+ version)  # Set window title
window.geometry(wingeoxlator('',wglst,'')) # send wglst to generate tk.geometry() string.
window.config(background='white') 	# Set window background color
window.columnconfigure([0,1,2,3,4], weight=0)
window.rowconfigure([0,1,2,3], weight=1)

main_frame = tk.Frame(window, )
###main_frame.grid(column=0,row=0,padx=2)
main_frame.grid(column=0,row=0,padx=0)
main_frame.columnconfigure([0,1,2,3,4], weight=1)
if sys.platform == "win32":
    window.iconbitmap(path_to_dat / "ico/mmc4w-ico.ico") # Windows
else:
    iconpng = tk.PhotoImage(file = path_to_dat / "ico/mmc4w-ico.png") # Linux
    window.iconphoto(False, iconpng) 			# Linux
#confparse.set('display','displaysize',str(window.winfo_screenwidth()) +','+ str(window.winfo_screenheight()) )
updateIni('display','displaysize',str(window.winfo_screenwidth()) +','+ str(window.winfo_screenheight()) )
window.update()

#nnFont = Font(family="Segoe UI", size=20)  		# Set the base font
fontfamily = confparse.get('display','fontfamily')
fontsize   = confparse.get('display','fontsize')
nnFont = Font(family=fontfamily, size=fontsize)		# Set the base font
btnwidth = int(confparse.get('mainwindow','buttonwidth')) - 1	# distinguish control buttons by making them a little smaller
padx   = confparse.get('mainwindow','padx')
pady   = confparse.get('mainwindow','pady')

#
# Set up text fields
#
# text1 contains the currnt song
text1 = tk.Text(main_frame, height=1, width=56, wrap= tk.WORD, font=nnFont)
text1.grid(column=0, columnspan=5, row=0, padx=padx, pady=pady)
# text2 is for the album / track
text2 = tk.Text(main_frame, height=1, width=35, wrap= tk.WORD, font=nnFont)
text2.grid(column=0, columnspan=3, row=1, padx=padx, pady=pady)
# text2 is for current elapsed position
text3 = tk.Text(main_frame, height=1, width=20, wrap= tk.WORD, font=nnFont)
text3.grid(column=3, columnspan=2, row=1, padx=padx, pady=pady)

#
# Define the fixed buttons
#
button_volup = tk.Button(main_frame, width=btnwidth, bg='gray90', text="Vol +", font=nnFont, command=volup)
button_volup.grid(column=0, sticky='', row=2, padx=padx, pady=pady)
button_voldn = tk.Button(main_frame, width=btnwidth, bg='gray90', text="Vol -", font=nnFont, command=voldn)
button_voldn.grid(column=0, sticky='', row=3, padx=padx, pady=pady)
button_pause = tk.Button(main_frame, width=btnwidth, bg='gray90', text="Play", font=nnFont, height=2, command=btnPlay)
button_pause.grid(column=1, sticky='', row=2, rowspan=2, padx=padx, pady=pady)
button_prev = tk.Button(main_frame, width=btnwidth, bg='gray90', text="<< Prev", font=nnFont, command=previous)
button_prev.grid(column=2, sticky='', row=2, padx=padx, pady=pady)
button_next = tk.Button(main_frame, width=btnwidth, bg='gray90', text="Next >>", font=nnFont, command=next)
button_next.grid(column=2, sticky='', row=3, padx=padx, pady=pady)

#
# add extra buttons for:
#
button_select = tk.Button(main_frame, width=btnwidth, bg='gray90', text="Select", font=nnFont, command=select)
button_select.grid(column=3, sticky='', row=2, padx=padx, pady=pady)
button_remove = tk.Button(main_frame, width=btnwidth, bg='gray90', text="Remove", font=nnFont, command=remove)
button_remove.grid(column=4, sticky='', row=2, padx=padx, pady=pady)
button_switches = tk.Button(main_frame, width=btnwidth, bg='gray90', text="SWITCHES", font=nnFont, command=switches)
button_switches.grid(column=3, sticky='', row=3, padx=padx, pady=pady)
button_exit = tk.Button(main_frame, width=btnwidth, bg='gray90', text="Quit", font=nnFont, command=exit)
button_exit.grid(column=4, sticky='', row=3, padx=padx, pady=pady)

#
# ADD BUTTONS FOR PLAYLISTS AND Radio buttons ============================
#
# Radio buttons are defined in the .ini file under [radio_buttons]. 
# Fields are:
#	name 		is used as the key to the related dictionaries
#	row, col	row and column in the display to place the button
#	type		"playlist" for local playlists, or "stream" for 
#				internet radio station streams
#	button_Text	label to display on the button
#	stream_URL 	(opt) URL of the stream, 
#	stream_Art	(opt) URL of artwork image
# format of:  playlist name = row, column, button text, type, stream_URL, stream_artwork 
# 	radio-italiafm = 9,1,Italia FM,stream,https://andromeda.shoutca.st/tunein/jdiflu00-stream.pls,
#
# The first 5 fields are required for all radio buttons; and if 
#    type is "stream" then stream_URL and stream_Art are also required (though art may be empty)
#
logger.debug("Loading radio button definitions")
btnwidth = confparse.get('mainwindow','buttonwidth')	# back to full size buttons
radioBtn = {}			# dictionary of TKinter radio buttons. key is the PLAYLIST NAME
playlistType = {}		# is it a playlist or stream
playlistName = {}		# Name on the button
playlistURL = {}		# dictionary of radio station stream URLs
playlistArt = {}		# dictionary of radio station artwork URLs
# btns contains the entire collectin of playlists button definitions from config section
btns = confparse.items('radio_buttons', raw=False, vars=None)
# confparse.items returned ALL the items at once, so we need to process each entry in that list, 
#	making each entry into its own dictionary containing a list of the individual fields.
#	No doubt there is a more elegant method
btnList = {}
for btnListStr in btns:
    btnPLname = btnListStr[0] 		# filename of the playlist - key to the dictionary
    btnList = str(btnListStr[1]).split(',')
#    logger.debug(f"btnPLname={btnPLname}, btnList={btnList}")
    btnRow  = btnList[0] 		# Row and Col where to show on the UI
    btnCol  = btnList[1]
    btnText = btnList[2] 		# text label to show on the button
    playlistName[btnPLname] = btnText		# Name on the button
    btnType = btnList[3] 		# text label to show on the button
    radioBtn[btnPLname] = tk.Button(main_frame, width=btnwidth, bg='gray90', text=btnText, font=nnFont, command=lambda btnPLname=btnPLname: loadplaylist(btnPLname) )
    radioBtn[btnPLname].grid(column=btnCol, sticky='', row=btnRow, padx=padx, pady=pady)
    playlistType[btnPLname] = btnType		# is it a playlist or stream

    # we need to save the station details for later
    if btnType == 'stream':
        playlistURL[btnPLname] = btnList[4]	# the URL of the stream for the radio station
        playlistArt[btnPLname] = btnList[5]	# the URL of the image for the radio station
    elif btnType == 'playlist':
        pass					# no additional info required
    else: 
        logger.info(f"Invalid radio button type '{btnType}' detected for {btnPLname} in configuration file")

#
# display artwork for track, album or station
#
#artwinilist = [300, 300]
artwinilist = cp.getlist('mainwindow','artimage')	# size of the album art image
artwinilist[0] = int(artwinilist[0]) 		# convert to integers
artwinilist[1] = int(artwinilist[1])
#logger.debug(f"integers    artwinilist[0]={artwinilist[0]}, artwinilist[1]={artwinilist[1]}")

aartvar = ''			# aartvar tells us whether or not to display the art window.
aart = artWindow(aartvar)	# artWindow prepares the image, 'configs' the Label and returns image as well.
aartLabel = tk.Label(main_frame, image=aart)
aartLabel.grid(column=3, columnspan=2, row=4, rowspan=7, padx=padx, pady=pady)

window.update()




#########################################################################
#									#
#									#
#			MAIN FUNCTIONS					#
#									#
#									#
#########################################################################

def volbtncolor(vol_int):  # Provide visual feedback on volume buttons.
    global lastvol, colrVolume, button_volup, button_voldn
#    logger.debug("volbtncolor({}) called with lastvol={}.".format(vol_int,lastvol) )
    if lastvol != str(vol_int):
        MPD('setvol',vol_int)
        lastvol = str(vol_int)
        updateIni('serverstats','lastvol',lastvol )
    logger.debug('Set volume to {}.'.format(vol_int))

    # update the colors of the Vol+ and Vol- buttons
    upconf = colrVolume[vol_int]
    button_volup.configure(text=upconf[0],bg=upconf[1],fg=upconf[2])
    button_voldn.configure(text=upconf[3],bg=upconf[4],fg=upconf[5])
    window.update()


#
# display the toggle switches
#
def displaySwitches():
    global window, button_switches
    #toggleSymbols = { 'random': "r", 'repeat': "p", 'consume': "c", 'single': "s" }
    toggleSymbols = { 'random': "rnd", 'repeat': "rpt", 'consume': "c", 'single': "s" }
    toggleStatus  = { 'random': 0,     'repeat': 0,     'consume': 0,   'single': 0 }
    for key in toggleStatus:
        toggleStatus[key] = float( currStatus[key] )	# update status, force to numeric
        if toggleStatus[key] == 0:
            toggleSymbols[key] = toggleSymbols[key].lower()
        else:
            toggleSymbols[key] = toggleSymbols[key].upper()
    msg = "{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'])
#    logger.debug("{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'],currPlaylist) )
    button_switches.configure(text=msg,bg='gray90')


def plupdate():
    global currPlaylist
    logger.debug("plupdate() called")
    cpl = client.listplaylists()
    if len(cpl) > 0:
        pl = ""
        for plv in cpl:
            pl = plv['playlist'] + "," + pl
        currPlaylist = confparse.get("serverstats","lastPlaylist")
        confparse.set("serverstats","playlists",str(pl))
        if currPlaylist == '':
            confparse.set('serverstats','lastPlaylist',cpl[0]['playlist'])
            currPlaylist = 'Select a saved playlist. "Look" menu.' # a backup strategy. 'Joined Server Queue' is primary.
        with open(iniFilename, 'w') as SLcnf:
            confparse.write(SLcnf)
    else:
        endWithError("No PlayList Found","The MPD server shows no saved playlist.")



#########################################################################
#									#
#	One of the radio buttons was pressed - load the playlist	#
#									#
# If a local playlist, just load <newPlaylist>.m3u file.		#
# For streaming sources, such as internet radio stations, MPD expects	#
#   an .m3u files containing only the URL of the stream. 		#
# We could create separate small files for each stream ... but we can 	#
#   easily load the Queue (currently playing playlist) from details 	#
#   conveniently stored in the configuatation .ini file. 		#
#########################################################################
#
def loadplaylist(newPlaylist):
    global currPlaylist, radioBtn, text3
    logger.debug(f"loadplaylist({newPlaylist}) called. currPlaylist={currPlaylist}.")
    MPD('clear')
    if currPlaylist != "":
        # first return the previous playlist' button to normal
        radioBtn[currPlaylist].configure(bg=colrButton)

#    logger.debug("playlistType={}, playlistURL={}.".format(playlistType, playlistURL ) )
#    logger.debug(f"playlistType[{newPlaylist}]={playlistType[newPlaylist]}." )
    if playlistType[newPlaylist] == 'playlist':
        MPD('load',newPlaylist)		# a static .m3u file already exists
    elif playlistType[newPlaylist] == 'stream':
        #
        # place the stream into the queue, without physically writing it to disk
        MPD('add',playlistURL[newPlaylist])
        logger.debug(f"add to queue.  full Playlist={client.playlistinfo()}.")
    else:
        logger.warning(f"Loadplaylist - unexpected playlistType '{playlistType[newPlaylist]}' for playlist '{newPlaylist}'")

    #
    # check for a problem with the playlist
    #	could have been deleted, or moved or radio invalid
    #
    MPD('play')				# MPD pauses when a new playlist loaded
    time.sleep(2)			# give MPD time to reject this playlist
					# may need to increase this on slower machines
    currStatus = client.status()
#    logger.debug(f"check for 'error' in currStatus={currStatus}")
    if 'error' in currStatus:
        msg = currStatus['error']
        logger.warning(f"MPD ERROR: {msg}.  playlist={currPlaylist}")
        messagebox.showinfo("MPD ERROR",msg)
        MPD('clear')
        currPlaylist = ""
        return				# don't action the error playlist

    logger.debug(f"{newPlaylist} seems ok, so updating.")
    # change background of the button for this playlist button
    radioBtn[newPlaylist].configure(bg=colrSelected)     # the active radio button

    #
    # have we also swapped between playlist and stream ?
    #	if so, disable appropriate buttons
    #
    if playlistType[newPlaylist] == 'stream':
        # radio doesn't need [Prev], [Next] or [Remove] buttons
        button_prev.configure( bg=colrDisabled, text=" ", command=btn_disabled)
        button_next.configure( bg=colrDisabled, text=" ", command=btn_disabled)
        button_remove.configure(bg=colrDisabled, text=" ", command=btn_disabled)
    else:
        # reinstate Prev and Next
        button_prev.configure( bg='gray90', text="<< Prev", command=previous)
        button_next.configure( bg='gray90', text="Next >>", command=next)
        button_remove.configure( bg='gray90', text="Remove", command=remove)

    window.update()

    updateIni("serverstats","lastPlaylist",newPlaylist )
    currPlaylist = newPlaylist

    logger.debug(f"loadplaylist end   currPlaylist={currPlaylist}.")



#
#	display the 'now playing' info for current playlist track
#
def displaytrack():
    global window, text1, text2, currSong
    logger.debug(f"displaytrack() called. len(currSong)={len(currSong)}" )
    msg1 = ""
    msg2 = ""

    if len(currSong) == 0:
        displayError("-- no track selected.  Choose a playlist --","")
        return

    if "title" in currSong:
        msg1 = currSong["title"]
    if "artist" in currSong:
        msg1 += " - "+ currSong["artist"]
#    logger.debug('displaytrack()  msg1={}, currSong["title"]={}, currSong["artist"]={}, currSong["album"]={}'.format( msg1, currSong["title"], currSong["artist"], currSong['album'] ) )
#    logger.debug('displaytrack()  msg1={}, currSong={}.'.format( msg1, currSong ) )
    # display now-playing track information or error message
    text1.delete("1.0", 'end')
    text1.insert("1.0", msg1)

    # second line is Album & track
    if 'album' in currSong:
        msg2 = currSong['album']
        if 'track' in currSong:
            msg2 += f" (track {currSong['track'].zfill(2)})"
    else:
        msg2 = "-- no album --"
    text2.delete("1.0", 'end')
    text2.insert("1.0", msg2)

    #
    # load artwork for the current track
    #
    aartvar = getaartpic(currSong)	# get artwork for currSong
    aart = artWindow(aartvar)		# artWindow prepares the image, 'configs' the Label and returns image as well.
    aartLabel.configure(image=aart)
    window.update()
    logger.debug(f" bottom of displaytrack.  window updated.  aartvar={aartvar}, aart={aart}")


#
#	display progress within the current track (elapsed time)
#
def displayprogress():
    global text3
    msg = ""
    if 'duration' in currStatus:
        dur = float(currStatus['duration']) 
        if 'elapsed' in currStatus:
            elap = float(currStatus['elapsed']) 
        else: elap = 0
        msg = f"{int(elap)} of {int(dur)} sec"
    # update text3
    text3.delete("1.0", 'end')
    text3.insert("1.0", msg)


#
#	display the 'now playing' info for current song on radio
#
def displayradio():
    global window, text1, text2, text3		#, currSong
    logger.debug(f"displayradio() called.    playlistName[{currPlaylist}]={playlistName[currPlaylist]}" )
    # display details from the current radio station
    if "title" in currSong:			# no error mesage,
        msg = currSong["title"]			# currenly playing song
#    elif "title" in currSong:			# no error mesage,
#        msg = currSong["title"]			# currenly playing song
#    else:
#        msg = currPlaylist			# if no station name, use the label
    # display now-playing track information or error message
    text1.delete("1.0", 'end')
    text1.insert("1.0", msg)

    # second line is name of radio station
    if "name" in currSong:
        msg = currSong["name"]		# name of the radio station
    else: msg = ""
    text2.delete("1.0", 'end')
    text2.insert("1.0", msg)

    # update text3
    text3.delete("1.0", 'end')
#    text3.insert("1.0", playlistName[currPlaylist]	# if no station name, use the label

    aart = ''
    logger.debug(f"displayradio  loading artwork   playlistArt[{currPlaylist}]={playlistArt[currPlaylist]}")
    if playlistArt[currPlaylist] != '':
        # load artwork from playlistArt[newPlaylist]
        aart = artWindowRadio( playlistArt[currPlaylist] ) 	# the URL of the image for the radio station
    aartLabel.configure(image=aart)
    window.update()
    logger.debug(f" bottom of displayradio.   aartvar={aartvar}, aart={aart}")



def displayError(msg1, msg2):
    global window, text1, text2, text3		#, currSong
#    logger.debug("displayradio({},{}) called.".format( msg, currSong ) )
    # if msg1 and/or msg2 are passed in, they are messages to diplay
    text1.delete("1.0", 'end')
    text1.insert("1.0", msg1)

    text2.delete("1.0", 'end')
    text2.insert("1.0", msg2)

    text3.delete("1.0", 'end')
#    text3.insert("1.0", playlistName[currPlaylist]	# if no station name, use the label




#########################################################################
#									#
#		Main program logic					#
#									#
#########################################################################
logger.debug(" ")
logger.debug("vvvvvvvvvv  Main program logic  vvvvvvvvvvvvvvv")

#
# display initial values from current MPD status 
#
# Note: Just because this program has just started does not mean that 
#	MPD must also have just started - MPD may already be playing, 
#	so we may have to catch up with what MPD is currently doing,
#	or determine initial position from the .ini file.
#
currStatus = MPD('status')		# getCurrStatus()  # get MPD's current status

displaySwitches()			# display the toggle switches

lastvol = currStatus["volume"]		# MPD defaults to 100 volume
vol_int  = confparse.get('serverstats','lastvol')
if vol_int != lastvol:			# in this case, .ini file is better
    # initial value of volume - check it is a multiple of 5
    vol_fives = int( (float(vol_int)+3)/5 )	# map 0-100 to range of 0-20
    vol_int = int(vol_fives * 5) 
    volbtncolor(int(vol_int)) 		# Provide visual feedback on volume buttons.
    logger.debug(f"set volume ... from .ini file vol_int={vol_int},  current MPD {lastvol}={lastvol}")

#logger.debug(f"Volume is {lastvol}, Random is {currStatus['random']}, Repeat is {currStatus['repeat']}." )
logger.debug(f"currPlaylist={currPlaylist},  currStatus={currStatus}.")		#,  playlistType[]={playlistType}")

if 'error' in currStatus:
    msg = currStatus['error']
    logger.info(f"MPD ERROR: {msg}.  playlist={currPlaylist}")
    messagebox.showinfo("MPD ERROR",msg)
    MPD('clearerror')
    currPlaylist = ""			# pretend no previous playlist

#
# MPD could already be playing or paused - let it continue
# MPD could be stopped - possibly already got a song loaded ready to press play
#	MPD cannot tell us what playlist it is currently playing, so assume the last
#

if currStatus['state'] == 'play':
    currPlaylist = confparse.get("serverstats","lastPlaylist")   ## the most recently loaded playlist.
    logger.debug(f"state is play")
else:
    # state is 'pause' or 'stop'
    if 'songid' in currStatus:
        # there is a song loaded  - ready to press [Play] 
        logger.debug(f"there is a songid.   currPlaylist={currPlaylist},  currStatus={currStatus}.")
        currPlaylist = confparse.get("serverstats","lastPlaylist")   ## the most recently loaded playlist.
    else:
        # MPD has no song loaded - so reload last playlist
        logger.debug(f"there is a no songid.   currPlaylist={currPlaylist},  currStatus={currStatus}.")
        newPlaylist = confparse.get("serverstats","lastPlaylist")   ## the most recently loaded playlist.
        loadplaylist(newPlaylist)

#
# highlight the initial playlist
if currPlaylist != "":
    radioBtn[currPlaylist].configure(bg=colrSelected) 
    if playlistType[currPlaylist] == 'stream':
        # radio doesn't need [Prev], [Next] or [Remove] buttons
        button_prev.configure( bg=colrDisabled, text=" ", command=btn_disabled)
        button_next.configure( bg=colrDisabled, text=" ", command=btn_disabled)
        button_remove.configure(bg=colrDisabled, text=" ", command=btn_disabled)
logger.debug(f"  after check playlist   currStatus['state']={currStatus['state']}. len(currSong)={len(currSong)}" )


#########################################################################
#									#
#		NOW PLAYING logic					#
#									#
#									#
#########################################################################
#
# Since this program only told MPD to start playing, it does not know 
# when the current song has finished playing, and so cannot update its
# "now playing" information.  
#
# The approach is to constantly monitor MPD, and update the display as needed. 
# But what if the user interrupts the current song by pressing another button ?
#
prevState = ''			# the previous currStatus['state']
prevSong = []			# the previous song
while True:			# currStatus['state'] == 'play':
    currStatus = client.status()		# update current MPD status
    currSong = client.currentsong()		# display the current song
    if 'title' in currSong:     dispSong = "title: " + currSong['title']
    elif 'name' in currSong:    dispSong = "name: " + currSong['name']
    elif 'file' in currSong:    dispSong = "file: " + currSong['file']
    else:		        dispSong = currSong		# f"len={len(currSong)}"
#        logger.debug(f"now_playing  currStatus={currStatus['state']}, currPlaylist={currPlaylist}, Song={dispSong}")
#        logger.debug(" ")
    logger.debug(f"now_playing  Playlist={currPlaylist}, Status={currStatus['state']}, currSong={dispSong}.")

    #
    # check whether play/pause/stop state has changed
    #
    if prevState != currStatus['state']:
        logger.debug(f"now_playing       state changed from '{prevState}' to {currStatus['state']}.")
        # state has changed, so update the play/pause button
        prevState = currStatus['state']
        if prevState == 'play':
	    # when MPD is currentl playing, want the button to offer [Pause]
            logger.debug(f"set button to Pause.")
            button_pause.configure(text='Pause',bg=colrButton,command=btnPause) # play/pause when playing
        else: 		# state may be 'pause' or stop
            logger.debug(f"set button to Play.")
            button_pause.configure(text='Play',bg=colrPaused,command=btnPlay)   # play/pause when paused

    #
    # check for an error
    #
    msg1 = ''
    msg2 = ''
    if 'error' in currStatus:
        msg2 = "MPD ERROR: " + currStatus['error']
        logger.debug( msg2 )
        currPlaylist = ""

    if currPlaylist == '':
        msg1 = f"-- Press one of the playlist buttons to start --"
    elif len(currSong) == 0:
        msg1 = f"-- Playlist '{currPlaylist}' selected.  Press [Play] to start playing --"

    if msg1 != '':			# an error was detected
        displayError(msg1,msg2)		# display error message
        window.update()
        time.sleep(2)
        continue			# skip to next while iteration

    #
    # if song has changed, (file: or title:) update the Now playing information
    #
    if currSong != prevSong:
        logger.debug(f">>> song changed to currSong={currSong}, playlistType[{currPlaylist}]={playlistType[currPlaylist]}.")
        # Local tracks and radio stations are displayed differently
        if playlistType[currPlaylist] == 'playlist':
            displaytrack()
        elif playlistType[currPlaylist] == 'stream':
            displayradio()
        else:
            logger.info(f"now_playing - unexpected playlistType '{playlistType[currPlaylist]}' for playlist '{currPlaylist}'")
        prevSong = currSong
        if 'title' in currSong:
            updateIni("serverstats","lastsongtitle",currSong['title'] )



    if playlistType[currPlaylist] == 'playlist':
         displayprogress()		# update the elapsed time each iteration

    window.update()
    time.sleep(2)

# should never get to end of loop, unless program has ended
logger.debug(" ")
logger.debug('######### SHOULD NEVER GET HERE')
logger.debug(f"-----=====<<<<<   Passing control to TKinter >>>>>=====----- currStatus={currStatus}, currSong={currSong}." )
logger.debug(" ")
window.mainloop()  # Run the (not defined with 'def') main window loop.
# From here on the program is driven by button presses detected by TKinter
