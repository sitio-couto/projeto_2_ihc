import numpy as np
import cv2
from time import sleep

def find_faces(webcam):
    try:
        ret, image = webcam.read()                                      #capture from webcam
    except:
        print("Something went wrong")
        exit(0)
    grayscaled_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)          # to greyscale
    faces = face_cascade.detectMultiScale(grayscaled_image, 1.3, 5)     # find faces in the image
    return len(faces)                                                   # return faces quantity


def rewind_video(buffer, webcam):
    print("Rewinding")
    i = 0
    for index, frame in enumerate(reversed(buffer)):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # to greyscale
        cv2.imshow('frame',gray)                        # show the frame frame
        # if the face comes back stop rewinding
        if (i % 10) == 9:
            if find_faces(webcam) > 0:
                return index
            else:
                cv2.waitKey(15)
        i += 1                                          # add to the counter
        cv2.waitKey(25)                                 # wait for 25ms
    return -1

def unrewind_video(buffer, index):
    print("Unrewinding")
    buffer_cut = buffer[300-index:]
    for frame in buffer_cut:
        cv2.imshow('frame',frame)                        # show the frame frame
        cv2.waitKey(25)                                 # wait for 25ms


def play_video(rewind_buffer, video, delay=25):
    ret, frame = video.read()               # get next frame
    # mantem o rewind buffer
    rewind_buffer.append(frame)
    if len(rewind_buffer) > MAX_REWIND:
        rewind_buffer.pop(0)

    cv2.imshow('frame',frame)               # show the frame
    cv2.waitKey(delay)                         # wait for 25ms


# Open the Haar Cascade
face_cascade = cv2.CascadeClassifier("cascade_face.xml")
# Open webcam
webcam = cv2.VideoCapture(0)
# Open video
video = cv2.VideoCapture('Britney Spears - ...Baby One More Time.mp4')

# wait for things to actually open
while not webcam.isOpened() and not video.isOpened():
    continue

# Const
MAX_REWIND = 300            # Max frames in rewind buffer
DELAY = 25
DELAY_MIN = 15

ret, frame = video.read()
FRAME_0 = frame             # First frame

# Vars
# rewinding = False
rewind_buffer = []
faces_amount = 0


while True:
    # Stay on frame 1
    cv2.imshow('frame', FRAME_0)

    # Until find faces
    while faces_amount == 0:
        faces_amount = find_faces(webcam)
        sleep(0.5)

    # Play the video while there are faces
    while faces_amount > 0:
        for _ in range(10):
            play_video(rewind_buffer, video)
        play_video(rewind_buffer, video, DELAY_MIN)
        faces_amount = find_faces(webcam)


    # if the faces disappear, rewind video
    index = rewind_video(rewind_buffer, webcam)

    #TODO When we run out of buffer go back to the main loop
    if index > 0:
        #before that, play again what was rewinded
        unrewind_video(rewind_buffer, index)
        continue
    else:
        rewind_buffer = []
        video.release()
        video = cv2.VideoCapture('Britney Spears - ...Baby One More Time.mp4')


webcam.release()
video.release()
cv2.destroyAllWindows()





#TODO create key press callback
