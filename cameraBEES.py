from picamera import PiCamera, Color
from time import sleep
from datetime import datetime as dt
from subprocess import check_call
import shutil

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 15
camera.annotate_background = Color('blue')
camera.annotate_foreground = Color('yellow')
timestamp = dt.now().strftime("%Y-%m-%d_%H.%M.%S.h264")
convCommand = '-add {0}.h264 {1}.mp4'.format(timestamp,timestamp)
srcroot = '/home/pi/Videos/%s' % timestamp
dstroot = '/media/pi/BEEVIDS'

camera.start_preview(alpha=200)
camera.start_recording(srcroot)
for i in range(6):
    timeElapS = float(i)*0.5
    camera.annotate_text = "Elapsed: 0:00:%s" % timeElapS
    sleep(0.5)
camera.wait_recording(3)
camera.stop_recording()
shutil.copy(srcroot, dstroot)
check_call(["MP4Box",convCommand], shell=True, cwd=dstroot)
camera.stop_preview()
