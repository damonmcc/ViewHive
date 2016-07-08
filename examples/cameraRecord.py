from picamera import PiCamera
from time import sleep

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 15

camera.start_preview(alpha=100)
camera.annotate_text = "Hello bees!"
camera.brightness = 70
camera.start_recording('/home/pi/Videos/videoEffects.h264')
sleep(10)
camera.stop_recording()
camera.stop_preview()
