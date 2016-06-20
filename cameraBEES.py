from picamera import PiCamera, Color
from time import sleep
from datetime import datetime as dt

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 15
camera.annotate_background = Color('blue')
camera.annotate_foreground = Color('yellow')
timestamp = dt.now().strftime("%Y-%m-%d_%H.%M.%S.h264")

camera.start_preview(alpha=200)
camera.start_recording('/home/pi/Videos/%s' % timestamp)
for i in range(20):
    timeElapS = float(i)*0.5
    camera.annotate_text = "Elapsed: 0:00:%s" % timeElapS
    sleep(0.5)
camera.wait_recording(3)
camera.stop_recording()
camera.stop_preview()
