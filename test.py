import cv2
from pygame import mixer

mixer.init()
mixer.music.load('deep_time.ogg')
video = cv2.VideoCapture('deep_time_20fps.mp4') # Open video
i = 0

print(len(mixer.music))

while True:
    ret, frame = video.read()
    cv2.imshow('frame', frame)
    cv2.waitKey(1)
    if not i%300: mixer.music.play(0, i*453/9066)
    # print(i)
