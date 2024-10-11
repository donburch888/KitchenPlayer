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
version = "0.3.0"
# 0.1.0 Sept 2024 - Initial conversion from mmc4w 
#		  - cut out all the threading and simplify timing
# 0.2.0 Oct 2024  - continued conversion.  Remove all pop-ip windows,
#		     menus and artwork. Ensure countdown working correctly,
#		     especially when pausing or changing playlist.
#		  - Add radio stations, including countdown radio.
#		  - 
# 0.3.0 Oct 2024  - First version on Github. add [Remove] function
#
# still to do:	- if radio station playing, hide [Prev], [Next] buttons
#		- add artwork
#		- pop-up to alter the toggle switches
#		- [Select] button to select artist or album within current playlist
#		- adjust screen formatting to fill entire 7" screen
#
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter.font import Font
#from PIL import ImageTk, Image
import datetime
from time import sleep
import sys
from configparser import ConfigParser
import os
import musicpd
import time
import logging
from collections import OrderedDict
from pathlib import Path

if sys.platform != "win32":
    import subprocess
else:
    # from win32api import GetSystemMetrics
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(0)
    ctypes.windll.user32.SetProcessDPIAware()


#global serverip,serverport
global tbarini,endtime,firstrun, confparse
global currstat, pstate, currsong, lastpl


#########################################################################
#									#
#	Constants definitions						#
#									#
#########################################################################

# colours used for buttons
colrButton = "grey90"			# default button colour
colrPaused = "green1"			# play/pause when paused
colrRadioSelected = "skyblue1"		# the active radio button
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
#	get initial Configuration from mmc4w.ini			#
#									#
#########################################################################
path_to_dat = Path(__file__).parent
mmc4wIni = path_to_dat / "mmc4w.ini"
workDir = os.path.expanduser("~")

# confparse is for general use for normal text strings.
# for example, confparse.get('serverstats','playlists') returns the string:
#	Raffaellas,radio-Amore_SoloMusica,Albums,Oldies,Opera,default,
confparse = ConfigParser()	# current value of mmc4w.ini file as a dict
confparse.read(mmc4wIni)

# cp is for use where lists are involved.
# for example cp.getlist('serverstats','playlists') returns the list:
#	['Raffaellas', 'radio-Amore_SoloMusica', 'Albums', 'Oldies', 'Opera', 'default', '']
cp = ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
cp.read(mmc4wIni)

if confparse.get('basic','installation') == "":
    confparse.set('basic','installation',str(path_to_dat))
if confparse.get('basic','sysplatform') == "":
    confparse.set('basic','sysplatform',sys.platform)

#
# start the logger
#
logLevel = confparse.get('program','loglevel').upper()
logtoggle = confparse.get('program','logging').upper()
if logtoggle == 'OFF':
    logLevel = 'WARNING'

if logLevel == "INFO":
    if os.path.isfile(path_to_dat / "mmc4w.log"):
        os.remove(path_to_dat / "mmc4w.log")

if logLevel == 'DEBUG':
    logging.basicConfig(
        filename=path_to_dat / "mmc4w_DEBUG.log",
        format="%(asctime)s - %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
        level=logging.DEBUG,
    )
elif logLevel == 'INFO':
    logging.basicConfig(
        filename=path_to_dat / "mmc4w.log",
        format="%(asctime)s - %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
        level=logging.INFO,
    )
else: 		# anything else defaults to 'WARNING':
    logging.basicConfig(
        filename=path_to_dat / "mmc4w.log",
        format="%(asctime)s - %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
        level=logging.WARNING,
    )
logger = logging.getLogger(__name__)
logger.info("     -----======<<<<  STARTING UP  >>>>======-----")
#logger.info("D0) sys.platform is {}".format(sys.platform))


if confparse.get("basic","firstrun") == '1':
    wglst = confparse.get("default_values","maingeo").split(',')
else:
    wglst = confparse.get("mainwindow","maingeo").split(',')
#tbarini = confparse.get("mainwindow","titlebarstatus")  # get titlebar status. 
#wglst[2] = wglst[2]     #### dont compensate for screen width
#wglst[3] = wglst[3]


#
# get MPD server details
#
serverlist = confparse.get('basic','serverlist')
serverip   = confparse.get('serverstats', 'lastsrvr')
serverport = confparse.get('basic','serverport')
#logger.info("don1 confparse basic returns  serverlist="+ serverlist +", serverip="+ serverip +"  serverport="+ serverport )
if serverlist == "":
    proceed = messagebox.askokcancel("Edit Config File","OK closes the app and opens mmc4w.ini for editing.")
    if proceed == True:
        if sys.platform == "win32":
            os.startfile(mmc4wIni)
        else:
            subprocess.run(["xdg-open", mmc4wIni])
        sys.exit()

if serverip == '':
    iplist = cp.getlist('basic','serverlist')
    serverip = iplist[0]
    confparse.set('serverstats','lastsrvr',serverip)
    messagebox.showinfo("Server Set","Current server is set to\n" + serverip)

if confparse.get('serverstats','lastport') != "":
    serverport = confparse.get('serverstats','lastport')
else:
    confparse.set('serverstats','lastport',serverport)


aartvar = 0     ## aartvar tells us whether or not to display the art window.
lastvol  = confparse.get('serverstats','lastvol')
# initial value of volume - check it is a multiple of 5
vol_fives = int( (float(lastvol)+3)/5 )		# map 0-100 to range of 0-20
lastvol = int(vol_fives * 5) 
firstrun = confparse.get('basic','firstrun')

pllist = cp.getlist('serverstats','playlists')	# the list of available playlists
lastpl = confparse.get("serverstats","lastsetpl")   ## the most currently loaded playlist.

if version != confparse.get('program','version'):
    #### should this be an error ???
    confparse.set('program','version',version )

# update all the .ini configuration parameters
with open(mmc4wIni, 'w') as SLcnf:
     confparse.write(SLcnf)



def endWithError(msg):
    messagebox.showinfo("UhOh",msg)
    sys.exit()
    window.destroy()


#########################################################################
#									#
#	Connect to MPD and LOAD INITIAL VALUES				#
#									#
#########################################################################
client = musicpd.MPDClient()	# create MPD client object
client.timeout = None		# network timeout in seconds (floats allowed), default: None
client.idletimeout = None	# timeout for fetching the result of the idle command is handled seperately, default: None
try:
#    logger.debug("D1| Initial connect to MPD at {} on port {}".format(serverip,serverport))
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
    logger.debug("Connect to MPD client successful")


		# currstat  is current value of dict client.status()
currstat = dict()		# define current MPD state as a dict
pstate = 'stop'			# the current playing state of MPD
		# currsong  is current value of dict client.currentsong()
currsong = dict()		# define current song as a dict
globsongtitle = ""



#########################################################################
#									#
#			System functions				#
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
        logger.debug("wingeoxlator({},{},{})".format(geostring,geovals,geolist) )
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


#
#	Check the connection to MPD server, and reconnect automatically if necesssary
#
# 	if unable to re-connect, we immediately exit via an end With Error
#
def connext():
    global serverip,serverport
#    logger.info("connext() " + serverip +", serverport="+ serverport )   ####

    try:
        client.ping()  # Use ping() to see if we're connected.
    except (musicpd.ConnectionError, ConnectionRefusedError,ConnectionAbortedError) as errvar:
        logger.debug("D1| Initial errvar: {}".format(errvar))
        if errvar == 'Already connected':
            pass
        else:
            try:
                logger.debug("D1| Try to reconnect to {} on port {}".format(serverip,serverport))
                client.connect(serverip, int(serverport))
            except  (ValueError, musicpd.ConnectionError, ConnectionRefusedError,ConnectionAbortedError) as err2var:
                if err2var == 'Already connected':
                    pass
                elif 'WinError' in str(err2var) or 'Not connected' in str(err2var):
                    endWithError("The server you selected is not responding. Edit mmc4w.ini to ensure the 'lastsrvr' IP address is for a running server.")
                else:
                    logger.debug("D1| Second level errvar: {}".format(err2var))
                    endWithError("The server you selected is not responding.\nEdit mmc4w.ini to ensure the 'lastsrvr' IP address is for a running server.")
    # if we got here connection is OK - otherwise we already did an endWithError !
    return


#
#	return the current status of the MPD server
#		If the connection has dropped, try to reconnect it
#
def getcurrstat():			# get client.status(), but check for existing connection
    ## Checks connection, then connects if necessary.
		# otherwise we immediately exit via an end With Error
    global serverip,serverport
#    logger.debug("getcurrstat() called" )

    try:
        currstat = client.status()
    except (musicpd.ConnectionError, ConnectionRefusedError,ConnectionAbortedError, musicpd.ProtocolError) as errvar:
        logger.info("getcurrstat() exception errvar={}".format(errvar))
        if errvar == 'Already connected':
            pass
        else:
            #
            # MPD is NOT currently connected, so reconnect and try again
            try:
#                logger.debug("D1| Try to reconnect to {} on port {}".format(serverip,serverport))
                client.connect(serverip, int(serverport))
            except  (ValueError, musicpd.ConnectionError, ConnectionRefusedError,ConnectionAbortedError) as err2var:
                if err2var == 'Already connected':
                    pass
                elif 'WinError' in str(err2var) or 'Not connected' in str(err2var):
                    endWithError("The server you selected has stopped responding. ")
                else:
                    logger.debug("D1| ***** getcurrstat() second level error {} *****".format(err2var) ) 
                    endWithError("The server you selected is not responding.")
        currstat = client.status()

    # if we got here connection is OK - otherwise we already did an endWithError !
#    logger.debug("getcurrstat() returns {}.".format(currstat) )
    return currstat


def exit():
    global pstate, client, window
    logger.info("EXIT() Connections closed. Playback stopped. Quitting.")
    client.stop()
    pstate = "stop"
    sleep(2)
    currstat = client.status()
    logger.info("after 1st attempt, client.status()={}".format(client.status()) )

    if currstat['state'] == 'play':
        client.stop()
        pstate = "stop"
        sleep(2)
#    sys.exit()				# sys.exit works for single thread, 
					# but tkinter needs the main window destroyed
        logger.info("after 2nd attempt, client.status()={}".format(client.status()) )
    sleep(2)
    window.destroy()				# close tkinter window, exiting the program
    logger.info("EXIT() ended. .")


def updateIni(section, key, value):
    confparse.set(section,key,value)
    with open(mmc4wIni, 'w') as SLcnf:
        confparse.write(SLcnf)
    logger.debug("ini file  section [{}] updated with {} = {}".format(section, key, value) )


#
#	Button definitions
#
def next():
    logger.info('next() called pstate={}'.format(pstate) )
    if pstate == 'pause':
        pause()
    else:
        connext()
    try:
        client.next()
    except musicpd.CommandError:
        client.play()
        client.next()
    getSong()

def previous():
    if pstate == 'pause':
        pause()
    else:
        connext()
    try:
        client.previous()
    except musicpd.CommandError:
        client.play()
        client.previous()
    getSong()



def volup():
    global lastvol
    vol_int = int(lastvol)
#    vpre = lastvol[:]
    if vol_int < 100:
        client.volume(+5)
        vol_int = vol_int + 5
        volbtncolor(vol_int)

def voldn():
    global lastvol
    vol_int = int(lastvol)
    if vol_int > 0:
        client.volume(-5)
        vol_int = vol_int - 5
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
    logger.info("togl({}) toggleStatus={}, toggleSymbols={},  msg={}".format(key,toggleStatus,toggleSymbols,msg) )
    displaytrack(msg,currsong)
    toggleStatus[key] = stat
    toggleSymbols[key] = symb


def toglsingle():
    togl('single')


#
# new pop-up windows
#

#
#	SELECT a new playlist, or an album, Artist or track from the current playlist
#
def select():
    logger.info("select() called - add code later !")
#button_select = tk.Button(main_frame, width=9, bg='gray90', text="Select", font=nnFont, command=select)


#
#	REMOVE the currently playing track from the playlist, and optionally log it 
#
# I have tried to add variety to my music collection, and this has included some
# tracks I personally am not keen on. Since the KitchenPlayer is working off a 
# copy of my complete music collection, it 
def remove():
    global client, currsong, currstat
    logger.info("remove() called - add code later !")
    if lastpl[:6] == "radio-":
        messagebox.showinfo("ERROR - Cannot remove from a radio station")
        return

    logger.info("remove() lastpl={}, currsong={}, currstat={}.".format(lastpl,currsong,currstat) )
    # determine which is the offending song
    if currsong['id'] != currstat['songid']:
        messagebox.showinfo("ERROR - SONG IDs DO NOT MATCH")
    songID = currstat['songid']
    filename = currsong['file']
    # confirm it is to be removed  
    if proceed = messagebox.askokcancel("R U sure ?","REMOVE {} ?".format(currsong['title']) ):
        # remove from the playlist
        client.deleteid(songID)
        client.save(lastpl)	#,replace)	# replace playlist file with modified version

        # delete the file from the music directory
        command = "execute('rm '"+ filename +"')"
        logger.info('    command={}'.format(command) )
        # log the file which was deleted (in case it should be reinstated manually later)

    # assuming that MPD has automatically started playing the next track, what is it ?
    currstat = getcurrstat()		# update all the current status
    currsong = getSong()			# check the current song
    logger.info("remove()   returns currsong={}".format(currsong) )


#
#	SWITCHES to display and optionally change the  toggles
#
def switches():
    global toggleSymbols
    logger.info("switches() called - add code later !")
# Toggle Random", command=toglrandom)
# Toggle Repeat", command=toglrepeat)
# Toggle Consume", command=toglconsume)
# Toggle Single", command=toglsingle)

    # and update the flags and switches
    msg = "{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'])
#    logger.info("{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'],lastpl) )
    button_switches.configure(text=msg,bg='gray90') 



#########################################################################
#									#
#	SETUP MAIN TKinter WINDOWS DEFINITIONS				#
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
#with open(mmc4wIni, 'w') as SLcnf:
#    confparse.write(SLcnf)
updateIni('display','displaysize',str(window.winfo_screenwidth()) +','+ str(window.winfo_screenheight()) )
window.update()

#nnFont = Font(family="Segoe UI", size=20)  		# Set the base font
fontfamily = confparse.get('display','fontfamily')
fontsize   = confparse.get('display','fontsize')
nnFont = Font(family=fontfamily, size=fontsize)		# Set the base font

#
# Set up text fields
#
# text1 contains the currnt song
text1 = tk.Text(main_frame, height=1, width=55, wrap= tk.WORD, font=nnFont)
text1.grid(column=0, columnspan=5, row=0, padx=1)
# text2 is for the album / track
text2 = tk.Text(main_frame, height=1, width=35, wrap= tk.WORD, font=nnFont)
text2.grid(column=0, columnspan=3, row=1, padx=1)
# text2 is for current elapsed position
text3 = tk.Text(main_frame, height=1, width=20, wrap= tk.WORD, font=nnFont)
text3.grid(column=3, columnspan=2, row=1, padx=1)

#
# Define the fixed buttons
#
button_volup = tk.Button(main_frame, bg='gray90', width=9, text="Vol +", font=nnFont, command=volup)
button_volup.grid(column=0, sticky='', row=2, padx=1, pady=3)
#button_pause = tk.Button(main_frame, bg='gray90', width=9, height=2, text="Play", font=nnFont, command=btnPlay)
button_pause = tk.Button(main_frame, bg='gray90', width=9, height=2, text=" ", font=nnFont)	# command added later
button_pause.grid(column=1, sticky='', row=2, padx=1, pady=3, rowspan=2)
button_voldn = tk.Button(main_frame, bg='gray90', width=9, text="Vol -", font=nnFont, command=voldn)
button_voldn.grid(column=2, sticky='', row=2, padx=1, pady=3)
button_prev = tk.Button(main_frame, width=9, bg='gray90', text="<< Prev", font=nnFont, command=previous)
button_prev.grid(column=0, sticky='', row=3, padx=1, pady=3)
button_next = tk.Button(main_frame, width=9, bg='gray90', text="Next >>", font=nnFont, command=next)
button_next.grid(column=2, sticky='', row=3, padx=1, pady=3)

#
# add extra buttons for:
#
button_select = tk.Button(main_frame, width=9, bg='gray90', text="Select", font=nnFont, command=select)
button_select.grid(column=3, sticky='', row=2, padx=1)
button_remove = tk.Button(main_frame, width=9, bg='gray90', text="Remove", font=nnFont, command=remove)
button_remove.grid(column=4, sticky='', row=2, padx=1)
button_switches = tk.Button(main_frame, width=9, bg='gray90', text="SWITCHES", font=nnFont, command=switches)
button_switches.grid(column=3, sticky='', row=3, padx=1)
button_exit = tk.Button(main_frame, width=9, bg='gray90', text="Quit", font=nnFont, command=exit)
button_exit.grid(column=4, sticky='', row=3, padx=1)

#
# ADD BUTTONS FOR PLAYLISTS AND Radio buttons ============================
#
# playlist radio buttons are defined in the wwc4m.ini file under [playlist_buttons] in 
# format of:  playlist name = Button text, row, column 
# 	eg: 	Raffaellas = 3, 0, Raffaellas
#
#logger.info("Loading playlist/radio button definitions")
radioBtn = {}		# dictionary of TKinter radio buttons. key is the PLAYLIST NAME
# btns contains the entire collectin of playlists button definitions from config section
btns = confparse.items('playlist_buttons', raw=False, vars=None)
# confparse.items returned ALL the items at once, so we need to process each entry in that list, 
#	making each entry into its own dictionary containing a list of the individual fields.
#	No doubt there is a more elegant method
btnList = []
for btnListStr in btns:
    btnPLname = btnListStr[0] 		# filename of the playlist - key to the dictionary
    btnList = str(btnListStr[1]).split(',')
#    logger.info("create button btnText={}, btnList({})={}".format(btnText,len(btnList),btnList) )
    btnRow  = btnList[0] 		# Row and Col where to show on the UI
    btnCol  = btnList[1] 
    btnText = btnList[2] 		# text label to show on the button
#    logger.debug("     btnRow={}, btnCol={}, btnText={}, loadplaylist({})".format( btnRow,btnCol,btnText,'"'+btnPLname+'"') )
    radioBtn[btnPLname] = tk.Button(main_frame, width=10, bg='gray90', text=btnText, font=nnFont, command=lambda btnPLname=btnPLname: loadplaylist(btnPLname) )
    radioBtn[btnPLname].grid(column=btnCol, sticky='', row=btnRow, padx=1, pady=1)

#
# now for the radio station buttons.
# 	We can't load a streaming radio directly, so build a dict of radio station details 
#	later we can create a pseudo playlist as required
#
# radio station buttons are defined in the wwc4m.ini file under [radio_buttons] 
#	in same format as playlist buttons, but add URL of the stream, and URL of artwork image
# format of:  playlist name = Button text, row, column, station_URL, station_artwork 
# 	radio-italiafm = 9,1,Italia FM,https://andromeda.shoutca.st/tunein/jdiflu00-stream.pls,
#
btns = confparse.items('radio_buttons', raw=False, vars=None)
radioStationURL = {}	# dictionary of radio station stream URLs
radioStationArt = {}    # dictionary of radio station artwork URLs
btnList = {}
for btnListStr in btns:
    btnPLname = btnListStr[0] 		# filename of the playlist - key to the dictionary
    btnList = str(btnListStr[1]).split(',')
#    logger.info("create button btnText={}, btnList({})={}".format(btnText,len(btnList),btnList) )
    btnRow  = btnList[0] 		# Row and Col where to show on the UI
    btnCol  = btnList[1] 
    btnText = btnList[2] 		# text label to show on the button
#    logger.info("     btnRow={}, btnCol={}, btnText={}, loadplaylist({})".format( btnRow,btnCol,btnText,'"'+btnPLname+'"') )
    radioBtn[btnPLname] = tk.Button(main_frame, width=10, bg='gray90', text=btnText, font=nnFont, command=lambda btnPLname=btnPLname: loadplaylist(btnPLname) )
    radioBtn[btnPLname].grid(column=btnCol, sticky='', row=btnRow, padx=1, pady=1)
    # we need to save the station details for later
    radioStationURL[btnPLname] = btnList[3]		# the URL of the stream for the radio station
    radioStationArt[btnPLname] = btnList[4]		# the URL of the image for the radio station

    window.update()



#########################################################################
#									#
#									#
#			MAIN FUNCTIONS					#
#									#
#									#
#########################################################################

#
#	Play / Pause button 
#
# One button is used to Play or Pause the music, with the button label changing as appropriate.
#
def btnPause():			# The user has pressed the Pause button
    global currstat, pstate, client, window, button_pause

    # While MPD may have 3 states ('stop', 'play' or 'pause'), the button only has two
    #		note it is theoretically possible for MPD to be controlled from
    #		another client, and so this player might be out of sync
    #		If so, we would have to constantly check client.status
    connext()				# check client connection still open
    client.pause() 		 	# pause MPD
    pstate = 'pause'
    # change the button label ready for the user to 'Play' and bg colour
    button_pause.configure(text='Play',bg=colrPaused,command=btnPlay)	# play/pause when paused
    window.update
    currstat = getcurrstat()		# update all the current status
    logger.debug("   btnPause() exiting with pstate={} and currstat['state']={}.".format(pstate,currstat['state']) )


def btnPlay():			# The user has pressed the Play button
    global currstat, pstate, client, window, button_pause
#    logger.info('btnPlay() called with currstat={}, pstate={})'.format(currstat,pstate) )
    connext()				# check client connection still open
    client.play()			# start MPD playing
    pstate = 'play'
    # change the button label ready for the user to 'Pause' and bg colour
    button_pause.configure(text='Pause',bg=colrButton,command=btnPause)	# play/pause when playing
    window.update

    currstat = getcurrstat()		# update all the current status
    logger.debug("   btnPlay() exiting with pstate={} and currstat['state']={}.".format(pstate,currstat['state']) )
    play_mode()			# play track(s) until pause is pressed



#
#	Play through the current playlist.
#
# MPD will continue playing the playlist without any attenton from us.
# The issue is that we want to show the user what track is currently playing. 
# If a playlist of tracks, we can find the duration of each song, so can sleep till 
#	the end of the current song, then check the new current song again...
#	But what if the user interrupts the current song by pressing another button ?
#	So we count the elapsed time of the song, checking every 2 seconds that 
#	it is still playing
# If the playlist is a radio station, we have much less information, and that is 
#	dependent on what the station provides. Keep checking the detail provided 
#	every second.
#
def play_mode():			# play the current track, and the next, and ...
    global pstate, currstat, currsong, lastpl
#    logger.info('play_mode() starting  lastpl={}, currstat={}, currsong={}'.format(lastpl,currstat,currsong) )
    while pstate == 'play':
        currstat = getcurrstat()		# update all the current status
        pstate = currstat["state"]
        currsong = getSong()			# check the current song
#        logger.info(" ")
#        logger.info('play_mode() while loop   len(currsong)={}, pstate={}, currstat[state]={}'.format(len(currsong),pstate,currstat['state']) )

        # countdown the rest of this song 
        if lastpl[:6] == "radio-":
            countradio()			# monitor the radio station
        else:
            countdown( currstat['songid'] )	# count track elapsed until songid changed

        pstate = currstat["state"]
        if pstate != 'play':			# MPD is no longer playing
            break				# exit the while loop

	# countdown only detected that client.status showed a different song had started
        # repeat the while loop

    # ended while loop because no longer playing
#    logger.info(" ")
#    logger.info('play_mode() after while loop   pstate={})'.format(pstate) )
#    logger.info(" ")



#########################################################################
#									#
#	get the current song, and display details			#
#									#
#########################################################################
#
def getSong():		# pass in the ID of the last known playing song. 
#    global globsongtitle,endtime,pstate,elap,firstrun,prevbtnstate,lastvol,toggleSymbols,lastpl, currsong
    global pstate, currstat, currsong, lastpl
#    logger.info(' = = = = = = getSong() called = = = = = = = = ' )
    currstat = getcurrstat()
    pstate = currstat['state']
    logger.debug('D2| getSong() called	 lastpl={},  currstat={}.'.format(lastpl,currstat) )

    msg = ''
    #
    # get the current song
    #
    currsong = client.currentsong()
#    logger.info("    getSong   client.currentsong returned {}".format(currsong) )
#    logger.debug('D2| Got currsong (client.currentsong()) with a length of {}.'.format(len(currsong)))

    if len(currsong) == 0:		# no song is currently selected
        client.stop()
        msg = "No song in the queue. Go find one."
        lastpl = confparse.get('serverstats','lastsetpl')

    if lastpl[:6] == "radio-":
        logger.info("***** radio station "+ lastpl)
        if 'title' in currsong:
            updateIni("serverstats","lastsongtitle",currsong['title'] )
        displayradio(msg,currsong)
    else:
#        logger.info('     got Next Song   currsong["id"]={}, currstat["songid"]={}, title={}.'.format(currsong['id'],currstat['songid'],currsong['title']) )
#        currsongID = currsong['id']		# this is the new "current" song
        updateIni("serverstats","lastsongtitle",currsong['title'] )
        displaytrack(msg,currsong)

    logger.info("getSong returning currsong={}, pstate={}".format(currsong,pstate) )
#    logger.info(" ")
    return currsong



#########################################################################
#									#
#	countdown to end of the current track, updating display		#
#									#
#########################################################################
#
# Since this program only tells MPD to start playing, it does not know when 
#	the current song has finished playing, and so cannot update its
#	"now playing" information.  We will have to find a way around this.
# Fortunately we know the current song's duration, and MPD's elapsed time; 
#	so we can count down.  Update the screen every 2 seconds
#
# In each iteration check that MPD is still playing
#
def countdown(currsongID):
    global currstat, pstate, window, text3		# the current play/pause state
    if 'duration' not in currstat:
        return					# nothing to countdown

    dur = float(currstat['duration']) 
    elap = 0
    if 'elapsed' in currstat:
        elap = float(currstat['elapsed']) 
    msg = ''
#    logger.info("       Countdown() called.  pstate={}, elap={}, dur={}".format(pstate,elap,dur) )

    #
    # count in 2 second steps.. Each step check MPD still playing and update display
    #
    while elap < (dur -2):		# return 2 seconds before end
        displayprogress(elap,dur)	# display progress (elap of dur) in text3

        time.sleep(2)  			# wait 2 second
        elap = elap + 2			# another 2 seconds has now elapsed

        # check that MPD is still playing.  
        #	user may have pressed [Pause] or another client stoped MPD
        currstat = client.status()	# check status each loop in case user has paused
        pstate = currstat['state']
#        logger.debug("          Countdown() loop    pstate={}, elap={} of {}, msg={}".format(pstate,elap,dur,msg) )
        if pstate != 'play': 
            break			# quit if MPD is no longer playing
        if lastpl[:6] == "radio-":	# has user swapped to playing radio ?
            return			# quit if MPD is no longer playing

    #
    # near the end, check more often
    #
    while currstat['songid'] == currsongID:
#        logger.debug("    waiting for current song to finish.  currstat['songid']={}, currsongID={}.".format(currstat['songid'],currsongID) )
        sleep(0.5)
        currstat = client.status()		# faster method to update status
        if currstat['state'] != 'play': break	# quit if MPD is no longer playing
    # When status changes (eg [Pause] button pressed), simply return
    #    to stop counting down the seconds. 
    logger.info("       countdown returning    pstate={}, elap={}, msg={}".format(pstate,elap,dur,msg) )
    return


# 
# radio has no duration, so keep checking every 2 seconds 
def countradio():
    global currstat, currsong, pstate, window, text3		# the current play/pause state

    while pstate == 'play':
        currsong = client.currentsong()
        displayradio('', currsong)	# update the display
        #
        # count in 2 second steps.. Each step check MPD still playing and update display
        #
        time.sleep(2)  			# wait 2 second

        # check that MPD is still playing.
        if lastpl[:6] != "radio-":	# has user swapped to playing tracks ?
            return			# quit if MPD is no longer playing
        #	user may have pressed [Pause] or another client stoped MPD
        currstat = client.status()	# check status each loop in case user has paused
        pstate = currstat['state']
#        logger.info("          Countradio() loop    pstate={}, ".format(pstate) )

    # When status changes (eg [Pause] button pressed), simply return
    #    to stop counting down the seconds. 
    logger.info("       countradio returning    pstate={}, ".format(pstate) )
    return



#########################################################################
#									#
#	update display details of the surrently selectted track		#
#									#
#########################################################################
#
def displaytrack(msg, currsong):
    global window, text1, text2
#    logger.info("displaytrack({},{}) called.".format( msg, currsong ) )

    if len(currsong) == 0:
        msg = "-- no track selected.  Choose a playlist --"
    elif msg == '':			# no error mesage,
					# so display the title and artist
#        logger.info('displaytrack()  currsong["title"]={}, currsong["artist"]={}, currsong["album"]={}'.format( currsong["title"], currsong["artist"], currsong['album'] ) )
        if "artist" in currsong:
            msg = currsong["title"] +" - "+ currsong["artist"]
        else:
            msg = currsong["title"]
    # display now-playing track information or error message
    text1.delete("1.0", 'end')
    text1.insert("1.0", msg)

    # second line is Album & track
    if 'album' not in currsong:
        msg = "-- no album --"
    else:
        msg = currsong['album']
        if 'track' in currsong:
            msg = msg + " - track {}".format(currsong['track'].zfill(2))
    text2.delete("1.0", 'end')
    text2.insert("1.0", msg)
    window.update()


def displayradio(msg, currsong):
    global window, text1, text2
#    logger.info("displayradio({},{}) called.".format( msg, currsong ) )

    if len(currsong) == 0:
        msg = "-- no track selected.  Choose a playlist --"
    elif "title" in currsong:			# no error mesage,
        msg = currsong["title"]			# currenly playing song
    else:
        msg = lastpl				# if no station name, use the label
    # display now-playing track information or error message
    text1.delete("1.0", 'end')
    text1.insert("1.0", msg)

    # second line is name of radio station
    if "name" in currsong:
        msg = currsong["name"]		# name of the radio station
    else:
        msg = lastpl
    text2.delete("1.0", 'end')
    text2.insert("1.0", msg)

    window.update()



def displayprogress(elap,dur):
    global text3
    # update text3
    msg=str('{} of {} sec'.format(int(elap),int(dur)) )
    text3.delete("1.0", 'end')
    text3.insert("1.0", msg)
    window.update()



def volbtncolor(vol_int):  # Provide visual feedback on volume buttons.
    global lastvol, colrVolume, button_volup, button_voldn
#    logger.info("volbtncolor({}) called with lastvol={}.".format(vol_int,lastvol) )
    if lastvol != str(vol_int):
        connext()
        client.setvol(vol_int)
        lastvol = str(vol_int)
        updateIni('serverstats','lastvol',lastvol )
#    logger.debug('Set volume to {}.'.format(vol_int))

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
    toggleStatus  = { 'random': 0,   'repeat': 0,   'consume': 0,   'single': 0 }
    for key in toggleStatus:
        toggleStatus[key] = float( currstat[key] )	# update status, force to numeric
        if toggleStatus[key] == 0:
            toggleSymbols[key] = toggleSymbols[key].lower()
        else:
            toggleSymbols[key] = toggleSymbols[key].upper()
    msg = "{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'])
#    logger.info("{} {} {} {}".format(toggleSymbols['random'],toggleSymbols['repeat'],toggleSymbols['single'],toggleSymbols['consume'],lastpl) )
    button_switches.configure(text=msg,bg='gray90')




def plupdate():
    global lastpl,firstrun
    logger.info("plupdate() called")
    connext()
    cpl = client.listplaylists()
    if len(cpl) > 0:
        pl = ""
        for plv in cpl:
            pl = plv['playlist'] + "," + pl
        #confparse.read(mmc4wIni)
        lastpl = confparse.get("serverstats","lastsetpl")
        confparse.set("serverstats","playlists",str(pl))
        if lastpl == '':
            confparse.set('serverstats','lastsetpl',cpl[0]['playlist'])
            lastpl = 'Select a saved playlist. "Look" menu.' # a backup strategy. 'Joined Server Queue' is primary.
        if firstrun == '1':
            confparse.set('basic','firstrun','0')
            firstrun = '0'
        with open(mmc4wIni, 'w') as SLcnf:
            confparse.write(SLcnf)
    else:
        endWithError("No PlayList Found","The MPD server shows no saved playlist.")





#########################################################################
#									#
#	One of the radio buttons was pressed - load the playlist	#
#									#
#########################################################################
def loadplaylist(plvar):
    global lastpl, radioBtn, text3
    logger.info('loadplaylist({}) called. lastpl {}'.format(plvar,lastpl) )
    connext()
    client.clear()
    # check that playlist exists.  It should normally, because it was predefined in the .ini file
    try:
        client.load(plvar)
    except:
        messagebox.showinfo("File Not Found","Could not find the selected playlist '{}.m3u'. \n Edit mmc4w.ini.".format(plvar) )
        # don't update anything !
        return

    # first return the previous playlist' button to normal
    if lastpl != "":
        radioBtn[lastpl].configure(bg="grey90")
    # change background of the button for this playlist button
    radioBtn[plvar].configure(bg=colrRadioSelected)     # the active radio button
    window.update()
    # clear the progress bar
    text3.delete("1.0", 'end')
    window.update()

    updateIni("serverstats","lastsetpl",plvar )
    lastpl = plvar
    btnPlay()				# start the music actually playing

#    logger.info("end of loadplaylist()")
#    logger.info(" ")
    btnPlay()				# start playing




#########################################################################
#									#
#		Main program logic					#
#									#
#########################################################################
logger.info(" ")
logger.info("vvvvvvvvvv  Main program logic  vvvvvvvvvvvvvvv")

#
# load current MPD status
#
currstat = getcurrstat()		# get MPD's current status
pstate = currstat["state"]

displaySwitches()			# display the toggle switches

lastvol = currstat["volume"]
volbtncolor(int(lastvol)) 			# Provide visual feedback on volume buttons.
#    logger.info('3) Volume is {}, Random is {}, Repeat is {}.'.format(lastvol,currstat['random'],currstat['repeat']))


#
# if system has rebooted, playlist may not be loaded
#
if currstat['playlistlength'] == '0':
    # nothing in the current playlist, so re-load the last playlist
    client.clear()
    # check that playlist exists.  It should normally, because it was predefined in the .ini file
    try:
        client.load(lastpl)
    except:
#        messagebox.showinfo("File Not Found","Could not find the selected playlist '{}.m3u'. \n Edit mmc4w.ini.".format(lastpl) )
        msg ="Playlist {} Not Found, Select another playlist".format(lastpl)
        logger.info("error loadong playlist {}.".format(lastpl) )
    else:
        # playlist has been loaded
        logger.info("after playlist {} loaded ... currstat={}".format(lastpl,currstat) )
#
# highlight the initial playlist
radioBtn[lastpl].configure(bg=colrRadioSelected) 
window.update()


#
# get current song and display initial values
#
currsong = getSong()		# check the current song and display
#logger.info("Main program logic... got currsong={}, pstate={}".format(currsong,pstate) )
if 'duration' in currstat:
    dur = float(currstat['duration']) 
    elap = 0
    if 'elapsed' in currstat:
        elap = float(currstat['elapsed']) 
    displayprogress( int(float(currstat['elapsed'])),int(float(currstat['duration'])) )

# initial value of play/pause
if pstate == 'play':
    btnPlay()
else:
    btnPause()


logger.info(" ")
logger.info("-----=====<<<<< Firstrun: {}. {}   Passing control to TKinter >>>>>=====-----".format(firstrun,pstate) )
window.mainloop()  # Run the (not defined with 'def') main window loop.
# From here on the program is driven by button presses detected by TKinter
