# watches for the board's signal of observers on the pi's GPIO22
import RPi.GPIO as GPIO

# https://raspberrypi.stackexchange.com/questions/12966/what-is-the-difference-between-board-and-bcm-for-gpio-pin-numbering
# GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN) # GPIO22 (pin 15)

# https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
# setup callbacks for when GPIO22 is:
#    HIGH - an observer was detected
#    LOW  - an observer left
def play_video():
    print 'Play the video!'
    # TODO resume the video
def stop_video():
    print 'Stop the video!'
    # TODO reverse the video
GPIO.add_event_detect(22, GPIO.RISING,  callback=play_video)
GPIO.add_event_detect(22, GPIO.FALLING, callback=stop_video)