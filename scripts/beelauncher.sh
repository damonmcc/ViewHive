#!/bin/sh
# beelauncher.sh
# place in /boot/, will be called by rc.local
# Action: 
navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd /home/pi/Documents/Python\ 3\ Projects/Bee\ Camera
sudo python cameraBEES.py
cd /
