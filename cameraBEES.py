from picamera import PiCamera, Color
from time import sleep
from datetime import datetime as dt
import subprocess
import shutil
import sys

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 15
camera.annotate_background = Color('grey')
camera.annotate_foreground = Color('purple')
timestamp = dt.now().strftime("%Y-%m-%d_%H.%M.%S")
srcfile = '%s.h264' % timestamp
convCommand = 'MP4Box -add {0}.h264 {1}.mp4'.format(timestamp,timestamp)
srcroot = '/home/pi/Videos/%s' % srcfile
dstroot = '/media/pi/BEEVIDS'
scriptroot = '/home/pi/Documents/Python 3 Projects/Bee Camera'

camera.start_preview(alpha=200)
camera.start_recording(srcroot, format='h264')
for i in range(6):
    timeElapS = float(i)*0.5
    camera.annotate_text = "Elapsed: 0:00:%s" % timeElapS
    sleep(0.5)
camera.wait_recording(3)
camera.stop_recording()
shutil.copy(srcroot, dstroot)
print(convCommand)
conv = subprocess.call(convCommand, shell=True,
                    cwd=dstroot)
conv_status = conv.wait()
#for line in iter(conv.stdout.readline, b''):
#    print (line)
    
p = subprocess.Popen("ls", shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     cwd=dstroot)
p_status = p.wait()
for line in iter(p.stdout.readline, b''):
    print (line)

print ("*** ls exit status/return code: ", p_status)
print ("*** conv exit status/return code: ", conv_status)
camera.stop_preview()
