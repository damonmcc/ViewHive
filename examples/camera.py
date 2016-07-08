from picamera import PiCamera
from time import sleep

camera = PiCamera()

camera.rotation = 180
camera.start_preview(alpha=100)
camera.start_recording('/home/pi/Video/video.h264')
sleep(10)
camera.stop_recording()
camera.stop_preview()
