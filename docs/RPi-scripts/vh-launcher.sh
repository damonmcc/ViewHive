#!/bin/sh
# VHlauncher.sh
# place in /boot/, will be called by rc.local
# Action: navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd /home/pi/ViewHive/viewhive
sudo python ViewHive.py
cd /