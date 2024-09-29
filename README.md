# KitchenPlayer
Simple touch-screen mpd player (for RasPi + python)

 Purpose: Most music players assume audiophile users 
       who will select each track or album to play ... 
       but I just want to turn on background music like 
       a radio, but without adverts or annoying DJs

 Scope: KitchenPlayer ONLY provides a simple UI for MPD, intended to 
       operate more like a car radio where user presses buttons 
       to start pre-defined playlists. 
![splayer](https://github.com/user-attachments/assets/1b83ca02-525e-4dce-8ef5-bd8381e5ea33)

       KitchenPlayer sends commands to MPD, which does all the
       heavy lifting ... maintaining database of tracks, 
       playlists and doing the playing.  To reduce the load on MPD, 
       KitchenPlayer determines the time for each track and counts seconds 
       until the track should have finished.

       Curating the music and other configuration is expected to done 
       independently from other PCs. A Windows-style .ini file is used 
       for most controllable parameters.
       I have 17000 tracks and several playlists already defined. 

 Target Hardware: is a Raspberry Pi with audio HAT and 7" touch screen.

 History:
       based on mmc4w.py - 2024 by Gregory A. Sanders (dr.gerg@drgerg.com)
       Minimal MPD Client for Windows - basic set of controls for an MPD server.
               mmc4w version "v2.1.0"

       his use case - however my use case is almost opposite.
       Consequently I have made major changes to the User Interface 
       and stripped out a lot of functionality.

       Massive thanks to Gregory saving me from starting from scratch 
       with the python code for interacting with TKinter and MPD. 
 
 Major changes:
       mmc4w is designed to take up as little screen space as possible 
       to get the job done - however my use case is almost opposite ...
       so splayer takes up the full 7" screen to have  large touch buttons.  
       I display a number of radio-style buttons for playlists and radio stations,

       Radio stations have several significant differences from playlists:
       (1)     Only one line is in the playlist file, which contains 
               the URL of the streaming radio station.
       (2)     There is no track duration, and so we need an alternative 
               to using a timer.
       (3)     There is no album artwork in the folder containing the music, 
               so we need a different mechanism to display station's artwork.  

 Prerequisites:
       splayer.py uses the python-musicpd, TKInter and PIL libraries; 
       which are assumed to already be installed on the RasPi.

