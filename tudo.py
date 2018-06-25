from pygame import mixer
from time import sleep
import cv2, serial


__FACES__ = 1
__LEDRG__ = 1

def find_faces(webcam):
    try:
        ret, image = webcam.read()                                      #capture from webcam
    except:
        print("Something went wrong")
        exit(0)
    grayscaled_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)          # to greyscale
    faces = face_cascade.detectMultiScale(grayscaled_image, 1.3, 5)     # find faces in the image

    if __FACES__ < 0: return len(faces)                                 # return faces quantity
    else: return __FACES__

def led_status():
    global board, serial

    if board.in_waiting:                      # Se houver novas entradas
        serial = board.read(board.in_waiting) # Le todas as novas entradas

    if __LEDRG__ < 0: return serial[-1]       # Retorna cor mais recente do led
    else: return __LEDRG__

def audio_speed(audio_buffer, faces_amount):
    global DELAY, SCAN_FACES, buffer_speed, base_time

    if faces_amount == 1:
        DELAY = 46
        SCAN_FACES = 6
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
            if find_faces(webcam) > 0 or led_status():
                return index

        i += 1                                          # add to the counter
        cv2.waitKey(DELAY)               # wait for 25ms

    return -1       # If surpasses buffer length, return to FRAME_0

def unrewind_video(rewid_buffer, audio_buffer, index):
    global DELAY, SCAN_FACES, MAX_REWIND, base_time, led
    print("Unrewinding")
    buffer_cut = rewind_buffer[len(rewind_buffer)-index:]
    base_time = audio_buffer[len(rewind_buffer)-index]
    mixer.music.play(0, base_time)

    i = 0;
    for frame in buffer_cut:
        i += 1
        if i == SCAN_FACES:
            find_faces(webcam)
            led = led_status()

        cv2.imshow('frame',frame)                       # show the frame frame
        cv2.waitKey(DELAY)                              # wait for 25ms

    return

def play_video(rewind_buffer, video, audio_buffer, faces_amount):
    global i, mute, DELAY, SCAN_FACES, base_time, old_faces_amount, multiplier

    ret, frame = video.read()                 # get next frame
    frame_time = (mixer.music.get_pos()/1000) + base_time  # get audio time for frame

    if mute:
       mixer.music.play()
       mute = 0

    # updates audio and video buffers
    rewind_buffer.append(frame)
    audio_buffer.append(frame_time)

    # check buffers for max capacity
    if len(rewind_buffer) > MAX_REWIND:
        rewind_buffer.pop(0)
        audio_buffer.pop(0)

    # if not (old_faces_amount == faces_amount):
    #     mixer.music.play(0, audio_speed(audio_buffer, faces_amount))
    #     old_faces_amount = faces_amount
    #     cv2.imshow('frame',frame)               # show the frame
    #     cv2.waitKey(1)                      # wait for 25m
    #     i = 0
    # else:
    #     i += 1
    cv2.imshow('frame',frame)               # show the frame
    # if i < FRAME_SKIP: cv2.waitKey(1)
    # else: cv2.waitKey(DELAY)
    cv2.waitKey(DELAY)


face_cascade = cv2.CascadeClassifier("cascade_face.xml") # Open the Haar Cascade
webcam = cv2.VideoCapture(0) # Open webcam
video = cv2.VideoCapture('deep_time_20fps.mp4') # Open video
board = serial.Serial('COM3', 115200)

# wait for things to actually open
while not webcam.isOpened() and not video.isOpened() and board.is_open:
    continue

# Globals
MAX_REWIND = 300            # Max frames in rewind buffer
DELAY = 46
SCAN_FACES = 6
FRAME_SKIP = 30
serial = [0]
led = 1

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
    # Until find faces or led is green
    while faces_amount == 0 and not led_status():
        faces_amount = find_faces(webcam)
        sleep(0.2)

    # Play the video while there are faces
    while (faces_amount > 0 or led):
        for _ in range(SCAN_FACES):
            play_video(rewind_buffer, video, audio_buffer, faces_amount)
        play_video(rewind_buffer, video, audio_buffer, faces_amount)
        led = led_status()
        faces_amount = find_faces(webcam)

    # if the faces disappear, rewind video
    index = rewind_video(rewind_buffer, webcam)

    #TODO When we run out of buffer go back to the main loop
    if index > 0 or led:
        #before that, play again what was rewinded
        unrewind_video(rewind_buffer, audio_buffer, index)
        continue
    else:
        rewind_buffer = []
        audio_buffer = []
        buffer_speed = 1
        base_time = 0
        led = 1
        mute = 1
        mixer.music.load('deep_time.ogg')
        video.release()
        video = cv2.VideoCapture('deep_time.mp4')


webcam.release()
video.release()
cv2.destroyAllWindows()





#TODO create key press callback
