#               Don's simple Kitchen Music Player

# Purpose: 
Most music players assume audiophile users who will select
each track or album to play ... 
However I just want to turn on background music like a radio, but
without adverts or annoying DJs. 

# Target Hardware: 
A Raspberry Pi with audio HAT and 7" touch screen.
The model of RasPi, audio device or screen can be altered. 

# Scope: 
I have 17000 music tracks and several playlists already defined; 
it would be pontless not to use them. 
KitchenPlayer ONLY provides a simple User Interface for MPD, 
like a car radio, where user presses a button to start a 
pre-defined playlist or streaming radio station. 

![splayer](https://github.com/user-attachments/assets/1b83ca02-525e-4dce-8ef5-bd8381e5ea33)

Kitchen Player sends commands to MPD, which does all the heavy lifting ... 
maintaining database of tracks, playlists and doing the playing. 

This is easy ... except that we would like to show what song 
is currently playing ... which requires us to keep checking MPD. 
To reduce the processing load of constantly checking MPD, 
KitchenPlayer determines the time for each track and counts 
seconds until the track should have finished.

A Windows-style .ini file is used for most controllable parameters.
Curating the music and other configuration is assumed to be
done independently from other PCs. 

# History:
based on mmc4w.py - 2024 by Gregory A. Sanders (dr.gerg@drgerg.com)
Minimal MPD Client for Windows - basic set of controls for an MPD server.
     mmc4w version "v2.1.0"

Greg designed mmc4w to take up minimal screen space on his desktop PC.
My use case is almost opposite - piority is ease-of-use for my
non-technical partner to use while cooking in the kitchen. 
Consequently I have made major changes to the User Interface 
and stripped out a lot of functionality.

Massive thanks to Gregory saving me from starting from scratch 
with the python code for interacting with TKinter and MPD. 
Also for dynamically changing the color of the volume buttons. 

# Major changes:
I have added streaming Radio Stations, which have several 
significant differences from playlists:
(1) Only one line is in the playlist file, which contains 
    the URL of the streaming radio station.
(2) There is no track duration, and so we need an alternative 
    to using a timer.
(3) There is no album artwork in the folder containing the music, 
    so we need a different mechanism to display station's artwork.  

# Prerequisites:
KitchenPlayer.py uses the python-musicpd, TKInter and PIL libraries; 
which are assumed to already be installed on the RasPi.

