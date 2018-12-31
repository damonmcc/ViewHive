#!/bin/bash
pid=$(pgrep nose2)
sudo kill -9 pid
#python /home/sun/workspace/c/src/server.py &
cd ..
cd ..
sudo nose2 viewhive.tests.test_ViewHive.ViewHiveTests.test_menuFULL
