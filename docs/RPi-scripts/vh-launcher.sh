#!/bin/sh
# vh-launcher.sh
# 
# Action: navigate to home directory, then to script directory,
# then execute python script in a terminal, then back home

cd /
cd /home/pi/ViewHive/viewhive
sudo python3 ViewHive.py
ret=$?
if [ $ret -ne 0 ]; then
	WID=$(xprop -root | grep "_NET_ACTIVE_WINDOW(WINDOW)"| awk  '{print $5}')
	xdotool windowfocus $WID
	xdotool key ctrl+shift+t
	wmctrl -i -a $WID
fi
cd /