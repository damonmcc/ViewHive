#!/bin/sh
# vh-launcher.sh
# place in /boot/, will be called by rc.local
# Action: navigate to home directory, then to script directory, then execute python script in a terminal, then back home

cd /
cd /home/pi/ViewHive/viewhive
sudo python3 ViewHive.py
cd /