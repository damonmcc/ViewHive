from picamera import PiCamera, Color
from time import sleep
from datetime import datetime as dt
import subprocess
import shutil
import sys
import os, errno
def silentremove(filename):
    try:
        os.remove(filename)
        print ("*** Deleted: ", filename)
    except OSError as e:
        if e.errno != errno.ENOENT: # no such file or directory
            raise # re-raise exception if a different error occured
#def savetoUSB(drivename):
#    try:
        
camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 30
#camera.resolution = (1296, 730)
#camera.framerate = 49
camera.annotate_background = Color('grey')
camera.annotate_foreground = Color('purple')
sleep(15)
timestamp = dt.now().strftime("%Y-%m-%d_%H.%M.%S")
srcfile = '%s.h264' % timestamp
convCommand = 'MP4Box -add {0}.h264 {1}.mp4'.format(timestamp,timestamp)
srcroot = '/home/pi/Videos/%s' % srcfile
dstroot = '/media/pi/BEEVIDS/'
codetroot = '/home/pi/Documents/Python 3 Projects/Bee Camera'
recRes = 0.01 # resolution of elapsed time counter (seconds)
recPeriod = 3 # Seconds to record
camera.start_preview(alpha=200)


# First copy custom schedule to wittyPi folders
print('*** Active on %s***\n' % timestamp)
os.system("sudo cp -v ./HVScript0.wpi /home//wittyPi/schedules/HVScript0.wpi")
os.system("sudo cp -v ./HVScript0.wpi /home/wittyPi/schedule.wpi")
if (os.path.exists(dstroot)==False):
    print("**! No USB Stoarge named BEEVIDS !**")
    quit()

camera.start_recording(srcroot, format='h264')
for i in range(recPeriod*int((1/recRes))):
    timeElapS = "%.2f" % round(float(i+1)*recRes, 3)
    camera.annotate_text = "{0}, Elapsed: {1}".format(dt.now().strftime("%Y-%m-%d %H:%M:%S"), timeElapS)
    sleep(recRes)
camera.annotate_text = "{0}, DONE".format(dt.now().strftime("%Y-%m-%d %H:%M:%S"))
camera.wait_recording(1)
camera.stop_recording()
shutil.copy(srcroot, dstroot)
print(convCommand)
conv = subprocess.Popen(convCommand, shell=True,
                    cwd=dstroot)
conv_status = conv.wait()
#for line in iter(conv.stdout.readline, b''):
#    print (line)
silentremove(srcroot)
silentremove("{0}{1}.h264".format(dstroot,timestamp))
p = subprocess.Popen("ls", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     cwd=dstroot)
p_status = p.wait()
for line in iter(p.stdout.readline, b''):
    print (line)
if conv_status==0:
    print ("*** Conversion complete ***")
else:
    print ("**! Conversion FAILED !**")
camera.stop_preview()
camera.close()

quit()
#
#
