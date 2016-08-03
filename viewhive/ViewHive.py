from ViewHiveUtil import *
from picamera import PiCamera, Color
from time import sleep
import subprocess
import shutil
import sys
import lirc
import os, errno
def silentremove(filename):
    try:
        os.remove(filename)
        print ("*** Deleted: ", filename)
    except OSError as e:
        if e.errno != errno.ENOENT: # no such file or directory
            raise # re-raise exception if a different error occured
def synchSchedule():
    # Copy local schedule file to wittyPi directories 
    os.system("sudo cp -v ./HVScript0.wpi /home/wittyPi/schedules/HVScriptIMPORT.wpi")
    os.system("sudo cp -v ./HVScript0.wpi /home/wittyPi/schedule.wpi")
    # Set wittyPi schedule with its runScript.sh
    print(subprocess.check_output(["sudo", "/home/wittyPi/runScript.sh"],
                              universal_newlines = True))
def waitforUSB(drivename):
    while os.path.exists(drivename) == False:
          print("Waiting for %s USB..." % drivename)
          wait(3)
    print("%s detected..."% drivename)
    timestamp = now()


camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 30
#camera.resolution = (1296, 730)
#camera.framerate = 49
camera.annotate_background = Color('grey')
camera.annotate_foreground = Color('purple')
sleep(5)
timestamp = now()
recRes = 0.01 # resolution of elapsed time counter (seconds)
#####
#
# 3600 seconds per hour
recPeriod = 10 # Seconds to record

dstroot = '/media/pi/BEEVIDS/'
coderoot = '/home/pi/ViewHive/viewhive/ViewHive'
#
#
#####



camera.start_preview(alpha=200)
# First copy custom schedule to wittyPi folders
print('*** Active on %s***\n' % timestamp)
synchSchedule()
waitforUSB(dstroot)
timestamp = now()
srcfile = '%s.h264' % timestamp
srcroot = '/home/pi/Videos/%s' % srcfile
convCommand = 'MP4Box -add {0}.h264 {1}.mp4'.format(timestamp,timestamp)

try:
    display = Display()
    print('Display started')
    display.welcome()
    print('Welcome started')
except:
    print('Display FAILED')
    print('Unexpected error: %s'%sys.exc_info()[0])

camera.start_recording(srcroot, format='h264')
camera.led = True
for i in range(recPeriod*int((1/recRes))):
    timeElapS = "%.2f" % round(float(i+1)*recRes, 3)
    camera.annotate_text = "{0}, Elapsed: {1}".format(now(), timeElapS)
    sleep(recRes)
camera.annotate_text = "{0}, DONE".format(dt.now().strftime("%Y-%m-%d %H:%M:%S"))
camera.wait_recording(1)
camera.stop_recording()
shutil.copy(srcroot, dstroot)
print(convCommand)
conv = subprocess.Popen(convCommand, shell=True,
                    cwd=dstroot)
conv_status = conv.wait()
if conv_status==0:
    print ("*** Conversion complete ***")
else:
    print ("**! Conversion FAILED !**")


silentremove(srcroot)
silentremove("{0}{1}.h264".format(dstroot,timestamp))
print("{0} contains:".format(dstroot))
p = subprocess.Popen("ls", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     cwd=dstroot)
p_status = p.wait()
for line in iter(p.stdout.readline, b''):
    print (line),
camera.stop_preview()
camera.close()
#
#
