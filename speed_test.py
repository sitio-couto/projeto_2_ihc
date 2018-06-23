import numpy as np
import cv2
from pygame import mixer
import time
from time import sleep

def audio_speed(audio_buffer, faces_amount):
    global DELAY, current_speed, base_time

    set_speed = speed_switch.get(faces_amount)

    mixer.music.load(file_switch.get(set_speed))
    multiplier = current_speed/set_speed
    DELAY = delay_switch.get(set_speed)
    current_speed = set_speed

    for int in audio_buffer: int *= multiplier

    base_time = (mixer.music.get_pos()/1000 + base_time)*multiplier

    return base_time


DELAY = 21
current_speed = 1
audio_buffer = []
def speed_switch(x): return {1:1, 2:1.5}.get(x, 2)
def file_switch(x):
    return {1:'deep_time.ogg', 1.5:'deep_time_x15.ogg',2:'deep_time_x20.ogg'}
def delay_switch(x): return {1:21, 1.5:14, 2:10}
tf = 5
t0 = time.time()
base_time = 0

for i in range(350):
    audio_buffer.append(10)

mixer.init()
mixer.music.load('deep_time.ogg')
mixer.music.play()

while True:

    if (audio_speed == 1) and (time.time() - t0 > tf):
        mixer.music.play(0, audio_speed(audio_buffer, 2))
        t0 = time.time()

    elif (audio_speed == 1.5) and (time.time() - t0 > tf):
        mixer.music.play(0, audio_speed(audio_buffer, 3))
        t0 = time.time()

    elif (audio_speed == 2) and (time.time() - t0 > tf):
        mixer.music.play(0, audio_speed(audio_buffer, 1))
        t0 = time.time()
