import numpy as np
import cv2
from pygame import mixer
from time import sleep

def find_faces(webcam):
    try:
        ret, image = webcam.read()                                      #capture from webcam
    except:
        print("Something went wrong")
        exit(0)
    grayscaled_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)          # to greyscale
    faces = face_cascade.detectMultiScale(grayscaled_image, 1.3, 5)     # find faces in the image

    return len(faces)                                 # return faces quantity

def audio_speed(audio_buffer, faces_amount):
    global DELAY, buffer_speed, base_time

    if faces_amount == 1:
        DELAY = 21
        SCAN_FACES = 1
        multiplier = buffer_speed/1
        buffer_speed = 1
        mixer.music.load('deep_time.ogg')
    elif faces_amount == 2:
        DELAY = 16
        SCAN_FACES = 10
        multiplier = buffer_speed/1.2
        buffer_speed = 1.2
        mixer.music.load('deep_time_x12.ogg')
    elif faces_amount == 3:
        DELAY = 12
        SCAN_FACES = 25
        multiplier = buffer_speed/1.4
        buffer_speed = 1.4
        mixer.music.load('deep_time_x14.ogg')
    else:
        DELAY = 9
        SCAN_FACES = 30
        multiplier = buffer_speed/1.6
        buffer_speed = 1.6
        mixer.music.load('deep_time_x16.ogg')

    for time in audio_buffer: time *= multiplier

    base_time = (mixer.music.get_pos()/1000 + base_time)*multiplier

    return base_time

def rewind_video(video_buffer, webcam):
    global DELAY
    print("Rewinding")

    mixer.music.stop() # stops audio playback

    i = 0
    for index, frame in enumerate(reversed(video_buffer)):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # to greyscale
        cv2.imshow('frame',gray)                        # show the frame frame
        # if the face comes back stop rewinding
        if (i % 5) == 4:
            if find_faces(webcam) > 0:
                return index

        i += 1                                          # add to the counter
        cv2.waitKey(DELAY)               # wait for 25ms

    return -1       # If surpasses buffer length, return to FRAME_0

def unrewind_video(rewid_buffer, audio_buffer, index):
    global DELAY, MAX_REWIND, base_time
    print("Unrewinding")
    buffer_cut = rewind_buffer[len(rewind_buffer)-index:]
    base_time = audio_buffer[len(rewind_buffer)-index]
    mixer.music.play(0, base_time)

    i = 0;
    for frame in buffer_cut:
        i += 1
        if i == SCAN_FACES: find_faces(webcam)
        cv2.imshow('frame',frame)                       # show the frame frame
        cv2.waitKey(DELAY)                              # wait for 25ms


def play_video(rewind_buffer, video, audio_buffer, faces_amount):
    global i, mute, DELAY, base_time, old_faces_amount, multiplier
    ret, frame = video.read()                 # get next frame
    frame_time = (mixer.music.get_pos()/1000) + base_time  # get audio time for frame

    # updates audio and video buffers
    rewind_buffer.append(frame)
    audio_buffer.append(frame_time)

    # check buffers for max capacity
    if len(rewind_buffer) > MAX_REWIND:
        rewind_buffer.pop(0)
        audio_buffer.pop(0)

    if mute:
       mixer.music.play()
       mute = 0

    if not (old_faces_amount == faces_amount):
        mixer.music.play(0, audio_speed(audio_buffer, faces_amount))
        old_faces_amount = faces_amount
        cv2.imshow('frame',frame)               # show the frame
        cv2.waitKey(1)                      # wait for 25m
        i = 0
    else:
        i += 1
        cv2.imshow('frame',frame)               # show the frame
        if i < 20: cv2.waitKey(1)                      # wait for 25ms
        else: cv2.waitKey(DELAY)



# Open the Haar Cascade
face_cascade = cv2.CascadeClassifier("cascade_face.xml")
# Open webcam
webcam = cv2.VideoCapture(0)
# Open video
video = cv2.VideoCapture('deep_time.mp4')

# wait for things to actually open
while not webcam.isOpened() and not video.isOpened():
    continue

# Const
MAX_REWIND = 300            # Max frames in rewind buffer
DELAY = 21
SCAN_FACES = 10

# Vars
# rewinding = False
rewind_buffer = []
faces_amount = 0
old_faces_amount = 0
# thumb = cv2.imread('thumb.png', cv2.IMREAD_COLOR)

# Guarda o momento do audio correspondente ao frame do buffer
audio_buffer = []
buffer_speed = 1
base_time = 0
mute = 1
i = 0

# Inicializa modulo e carrega arquivo de som
mixer.init()
mixer.music.load('deep_time.ogg')

while True:

    # Until find faces
    while faces_amount == 0:
        # cv2.imshow('frame', thumb)
        # cv2.waitKey(DELAY)
        faces_amount = find_faces(webcam)
        sleep(0.2)

    # Play the video while there are faces
    while faces_amount > 0:
        for _ in range(SCAN_FACES):
            play_video(rewind_buffer, video, audio_buffer, faces_amount)
        play_video(rewind_buffer, video, audio_buffer, faces_amount)
        faces_amount = find_faces(webcam)


    # if the faces disappear, rewind video
    index = rewind_video(rewind_buffer, webcam)

    #TODO When we run out of buffer go back to the main loop
    if index > 0:
        #before that, play again what was rewinded
        unrewind_video(rewind_buffer, audio_buffer, index)
        continue
    else:
        rewind_buffer = []
        audio_buffer = []
        buffer_speed = 1
        base_time = 0
        mixer.music.load('deep_time.ogg')
        mute = 1
        video.release()
        video = cv2.VideoCapture('deep_time.mp4')


webcam.release()
video.release()
cv2.destroyAllWindows()





#TODO create key press callback
