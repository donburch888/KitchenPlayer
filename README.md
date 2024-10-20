#       Don's simple Kitchen Music Player

Most music players assume audiophile users who will select
each track or album to play ... 
However I just want a simple music player for my partner in the kitchen, 
so she can listen to background music like a radio, but without adverts or annoying DJs. 

# Operation: 
KitchenPlayer is a client for MPD, featuring buttons for playlists 
and internet radio stations and displaying 'now playing' information

![remmina_RasPi4 VNC_192 168 1 90_20241019-211445](https://github.com/user-attachments/assets/190864e2-1ab3-4bc0-8a6f-a56cc3929f63)

Fields at the top display the currently playing track (song Title and Artist);
the Album and Track number (if known); the elapsed playing time and song duration; 
and album art if available.

When playing an internet radio station however we can only display the limited now playing 
information supplied by the station; there is no artwork for the individual songs; 
and [< Previous] and [Next >] buttons are irrelevant.

The [Vol -] and [Vol +] buttons also use colour to indicate the current volume level, and the labels change to show the current value (40 out of 100 in this screen image).

When paused, the [Play] button changes to green to remind the user to press [Play] to resume.

The currently playing playlist is indicated by the playlist button being coloured.

![remmina_RasPi4 VNC_192 168 1 90_20241019-210127](https://github.com/user-attachments/assets/373aa23c-78ca-4a67-8a41-d4ae6b8ebcfd)

## Extra Buttons
[Quit] sends a stop to MPD and exits the KitchenPlayer program.  
I may remove this in future, since KitchenPlayer is intended to be dedicated

Current status of Random play, Repeat, and Consume modes are shown on the status button [RND rpt s c]. I have still to program the ability to change these settings by pressing the button.

[Select] is yet to be programmed to allow selection of a desired Artist or Album within the current playlist. 

[Remove] button  will remove the currently playing song from the playlist and music database. 
Why ? Because I have 17000 tracks collected from various sources over many years, 
and honestly some are not things I ever want to hear again. 


### There is intentionally no ability to curate the music collection.  
I assume that creating playlists and maintaining the music collection will be 
done using appropriate tools on a different PC by someone with more technical background. 


![remmina_RasPi4 VNC_192 168 1 90_20241019-210241](https://github.com/user-attachments/assets/44f95222-8aa5-4df1-ab3c-87830eb741a4)

======================================================================

# Technical details
Kitchen Player sends commands to MPD, which does all the heavy lifting ... 
maintaining database of tracks, playlists and doing the playing. 

This is easy, except that we would like to show what song 
is currently playing ... which requires us to keep checking MPD. 

Curating the music and other configuration is assumed to be
done independently from other PCs. 

A Windows-style .ini file is used for most controllable parameters.

## Target Hardware: 
My KitchenPlayer runs on a dedicated Raspberry Pi 4 with IQ Audio HAT and 7" touch screen 
though I believe it can moderately easily be adapted for other hardware. 
It is programmed in python, and uses TKinter, PIL and python-musicpd libraries. 

## Pre-requisites:
The hardware (audio and display) must first be installed and setup correctly.
MPD must already be installed and configured (as per the md.conf file). 
KitchenPlayer.py uses TKinter, PIL and python-musicpd libraries; which are assumed to already be installed on the RasPi.

# Configuration:
A windows-style .ini file named KitchenPlayer.ini is used for many controllable parameters. Important sections are:

    [basic] contains program location, MPD server
    [program] contains version and logging details. 'logging' should normally be on, with 'loglevel' set to 'info'
    [display] contains details of screen size, font and button size
    [mainwindow] defines the position and size of the main window - not needed if full screen -
    [searchwin] - not currently used - position of location & size for the pop-up for [Select] function
    [radio_buttons] details of all the radio-style buttons to load local playlists and streaming radio stations. Each comprises:
       name            is used as the key to the related dictionaries
       row, col        row and column in the display to place the button
       type            "playlist" for local playlists, or "stream" for internet radio station streams
       button_Text     label to display on the button
       stream_URL      (opt) URL of the stream,
       stream_Art      (opt) URL of artwork image

    eg radio-italiafm = 9,1,Italia FM,stream,https://andromeda.shoutca.st/tunein/jdiflu00-stream.pls,

The first 5 fields are required for all radio buttons; and if type is "stream" then stream_URL is required and stream_Art is optional

## screen layout
Refer to layout in the screen shots above.  A TKinter grid (currently 
10 rows x 5 columns) is used (starting from (0,0) in top left corner). 

To make it easy to change playlists and radio stations without 
having to go into the program code,  the position of the radio buttons 
is in the KitchenPlayer.ini configuration file. Note that the .ini file format 
does not allow spaces or tab characters between fields; so if you 
use them to help ensure you have entered everything, remember to 
remove all except around the equals sign before you save the .ini file. 

If you want to adjust the screen size or layout, look first at the [mainwindow] 
section in the KitchenPlayer.ini file.  'maingeo' supplies the window 
size and position, 'artimage' is the size of the album art (in pixels), 
and 'padx' and 'pady' specify the spacing between the radio buttons. 
'buttonwidth' is a TKinter setting for the width of the buttons (in characters) - 
but that seems independent of the font used for the text on the buttons
(specified in 'fontfamily' and 'fontsize' in the [display] section).

For more involved changes, it should be pretty easy to move other 
buttons around in the program code.  I am fairly new with python 
so my code shouldn't be too obscure, and I have tried to use 
meaningful variable and function names, and add plenty of comments 
in the program code. 

## Playlists and streaming radio stations
MPD makes a distinction between the 'Queue' (list of songs currently
loaded in memory) and a 'Playlist' (file stored on physical media).

MPD can load a local playlist.m3u file located in the playlists directory 
defined in the MPD mpd.conf file.  Internet radio 
(and other streaming sources) can also be defined in .m3u files
containing only the URL of the streaming source.

I have used an alternate approach of loading a URL directly into MPD from stream_URL 
conveniently stored in the KitchenPlayer.ini file. 

Some MPD commands require a URI, but MPD generally assumes the music_directory, and appears unable to supply the URI for the current song, so I have duplicated settings from the mpd.conf file into the [basic] section

     music_directory = /mnt/Media/Music
     playlist_directory = /var/lib/mpd/playlists
Note: my music is on a shared network drive, hence my non-standard music_directory

## Artwork
KitchenPlayer looks first for artwork embedded in the song file;
then for album art (searching the directory the file resides in for a file called
cover.png, cover.jpg, or cover.webp) and copies to cover.png in the KitchenPlayer program directory. 
If these fail to locate artwork, I have added to look for 'folder.jpg' in the folder containing the song, 
or in the parent folder. 

Artwork for radio streams is downloaded from the URL specified in the 
'stream_Art' parameter for the radio station in the KitchenPlayer.ini configuration file

# History:
KitchenPlayer is based on mmc4w.py - 2024 by Gregory A. Sanders (dr.gerg@drgerg.com)
Minimal MPD Client for Windows - basic set of controls for an MPD server.
     mmc4w version "v2.1.0"

Greg designed mmc4w to take up minimal screen space on his desktop PC.
My use case is almost opposite - however massive thanks to Gregory saving me from starting from scratch 
with the python code for interacting with TKinter and MPD. 
Also for dynamically changing the colour of the volume buttons. 

## Major changes:
- major changes to display layout and functionality.
- I have added streaming Radio Stations, which have several significant differences from playlists:
- changed to checking MPD status every time through the main loop (since MPD could receive commands from other clients).
