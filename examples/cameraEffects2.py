from picamera import PiCamera, Color
from time import sleep

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920, 1080)
camera.framerate = 15
camera.annotate_background = Color('blue')
camera.annotate_foreground = Color('yellow')

camera.start_preview(alpha=200)
camera.start_recording('/home/pi/Videos/videoEffects.h264')
for i in range(100):
    camera.annotate_text = "Hello bees! %s" % i
    camera.brightness = i
    sleep(0.1)
camera.stop_recording()
camera.stop_preview()
