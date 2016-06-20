from picamera import PiCamera, Color
from time import sleep
from datetime import datetime as dt
from subprocess import call
import shutil

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 15
camera.annotate_background = Color('blue')
camera.annotate_foreground = Color('yellow')
timestamp = dt.now().strftime("%Y-%m-%d_%H.%M.%S.h264")
convCommand = "MP4Box -add {0}.h264 {1}.mp4".format(timestamp,timestamp)
srcroot = '/home/pi/Videos/%s' % timestamp
dstroot = '/media/pi/BEEVIDS'

camera.start_preview(alpha=200)
camera.start_recording(srcroot)
for i in range(20):
    timeElapS = float(i)*0.5
    camera.annotate_text = "Elapsed: 0:00:%s" % timeElapS
    sleep(0.5)
camera.wait_recording(3)
camera.stop_recording()
shutil.copy(srcroot, dstroot)
call("cd", "dstroot")
call([convCommand])
camera.stop_preview()
