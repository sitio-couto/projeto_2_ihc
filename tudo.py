from pygame import mixer
from time import sleep
import cv2, serial


__FACES__ = -1
__LEDRG__ = 0

def find_faces(webcam):
    global __FACES__

    try:
        ret, image = webcam.read()                                      #capture from webcam
    except:
        print("Something went wrong")
        exit(0)
    grayscaled_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)          # to greyscale
    faces = face_cascade.detectMultiScale(grayscaled_image, 1.3, 5)     # find faces in the image

    if __FACES__ < 0: return len(faces)                                 # return faces quantity
    else: return __FACES__


def audio_speed(faces_amount):
    global VIDEO_DELAY, SCAN_FACES, buffer_speed, base_time, audio_length

    if faces_amount <= 1:
        VIDEO_DELAY = 43
        SCAN_FACES = 7
        multiplier = buffer_speed/1
        buffer_speed = 1
        audio_length = 453
        mixer.music.load('deep_time.ogg')
    elif faces_amount == 2:
        VIDEO_DELAY = 32
        SCAN_FACES = 30
        multiplier = buffer_speed/1.2
        buffer_speed = 1.2
        audio_length = 377
        mixer.music.load('deep_time_x12.ogg')
    elif faces_amount == 3:
        VIDEO_DELAY = 31
        SCAN_FACES = 30
        multiplier = buffer_speed/1.4
        buffer_speed = 1.4
        audio_length = 323
        mixer.music.load('deep_time_x14.ogg')
    else:
        VIDEO_DELAY = 20
        SCAN_FACES = 30
        multiplier = buffer_speed/1.6
        buffer_speed = 1.6
        audio_length = 283
        mixer.music.load('deep_time_x16.ogg')

    base_time = get_audio_checkpoint()

    return base_time

def rewind_video(video_buffer, webcam):
    global DELAY, frame_count, divider, buffer_speed, old_faces_amount, faces_amount, base_time
    print("Rewinding")

    mixer.music.stop() # stops audio playback
    buffer_speed = -1

    for index, frame in enumerate(reversed(video_buffer)):
        replay_frame(frame)
        if update_playback_data(): return index

    return -1       # If surpasses buffer length, return to FRAME_0

def unrewind_video(rewid_buffer, index):
    print("Unrewinding")
    buffer_cut = rewind_buffer[len(rewind_buffer)-index:]

    for frame in buffer_cut:
        update_playback_data();
        display_frame(frame)

    return

def play_video(rewind_buffer, video, faces_amount):

    ret, frame = video.read()   # get next frame
    rewind_buffer.append(frame) # updates video buffer

    # check buffers for max capacity
    if len(rewind_buffer) >= MAX_REWIND:
        rewind_buffer.pop(0)

    update_playback_data(); # Updates faces, LED and audio speed
    display_frame(frame)    # Show frame
    return

def update_playback_data():
    global SCAN_FACES, i, led, old_faces_amount, faces_amount
    audio_updated = False
    i += 1

    if (i % SCAN_FACES) == 0:
        led = led_status()
        faces_amount = find_faces(webcam)

        if not (old_faces_amount == faces_amount):
            mixer.music.play(0, audio_speed(faces_amount))
            old_faces_amount = faces_amount
            audio_updated = True

    return audio_updated # Returns 1 if updates

def replay_frame(frame):
    global DELAY, frame_count

    frame_count -= 1
    gray = cv2.cvtColor(add_observers(frame), cv2.COLOR_BGR2GRAY)  # to greyscale
    cv2.imshow('frame', gray)                        # show the frame frame
    cv2.waitKey(DELAY)               # wait for 25ms
    return

def display_frame(frame):
    global DELAY, frame_count

    sync_video()
    frame_count += 1
    cv2.imshow('frame', add_observers(frame))    # show the frame frame
    cv2.waitKey(DELAY)                           # wait for DELAY
    return

def add_observers(frame):
    global faces_amount, buffer_speed

    frame_copy = frame.copy()

    if buffer_speed > 0 and faces_amount == 0:
        observers = 1
    else:
        observers = faces_amount

    text = "OBSERVERS: " + str(observers) + " (x" + str(float(buffer_speed)) + ")"
    cv2.putText(frame_copy, text, (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0))

    return frame_copy

def led_status():
    global board, serial, __LEDRG

    if board.in_waiting:                      # Se houver novas entradas
        serial = board.read(board.in_waiting) # Le todas as novas entradas

    if __LEDRG__ < 0: return serial[-1]       # Retorna cor mais recente do led
    else: return __LEDRG__

def sync_video():
    global AUDIO_DELAY, VIDEO_DELAY, DELAY, buffer_speed

    DELAY = VIDEO_DELAY
    delay = get_audio_time() - get_audio_checkpoint()

    if abs(delay) > AUDIO_DELAY: print('SYNC|',buffer_speed,'| frame: ', frame_count, ' | delay: ', delay)

    if delay < -(AUDIO_DELAY):
        sleep(abs(delay))
    elif delay > AUDIO_DELAY:
        DELAY = 1

    return

def get_audio_checkpoint():
    global frame_count, audio_length
    return (frame_count*audio_length/9066)

def get_audio_time():
    global base_time
    return (mixer.music.get_pos()/1000) + base_time

def fade_out (img1, img2, len=10): #pass images here to fade between
    for IN in range(0,len):
        fadein = IN/float(len)
        dst = cv2.addWeighted(img1, 1-fadein, img2, fadein, 0)
        cv2.imshow('frame', dst)
        cv2.waitKey(1)

################################################################################

face_cascade = cv2.CascadeClassifier("cascade_face.xml") # Open the Haar Cascade
webcam = cv2.VideoCapture(0) # Open webcam
video = cv2.VideoCapture('deep_time_20fps.mp4') # Open video
board = serial.Serial('COM3', 115200)

thumb = cv2.imread('thumbnail.png', cv2.IMREAD_COLOR)
frame_0 = cv2.imread('frame_0.png', cv2.IMREAD_COLOR)

# Globals
MAX_REWIND = 300            # Max frames in rewind buffer
VIDEO_DELAY = 43
AUDIO_DELAY = 0.1
DELAY = 43
SCAN_FACES = 7
FRAME_SKIP = 30
serial = [0]
led = 1

rewind_buffer = []
faces_amount = 0
old_faces_amount = 0
frame_count = 0

# Guarda o momento do audio correspondente ao frame do buffer
audio_length = 453
buffer_speed = 1
base_time = 0
i = 0

# Inicializa modulo e carrega arquivo de som
mixer.init()
mixer.music.load('deep_time.ogg')

# wait for things to actually open
while not webcam.isOpened() and not video.isOpened() and board.is_open:
    continue

while True:
    # Until find faces or led is green
    while faces_amount <= 0 and not led_status():
        cv2.imshow('frame', thumb)
        cv2.waitKey(1)
        faces_amount = find_faces(webcam)
        if (faces_amount > 0 or led_status()):
            fade_out(thumb, frame_0, 30);
        else: sleep(0.2)

    # Play the video while there are faces
    while (faces_amount > 0 or led):
        play_video(rewind_buffer, video, faces_amount)
        # if frame_count == 9066:

    # if the faces disappear, rewind video
    index = rewind_video(rewind_buffer, webcam)

    # When we run out of buffer go back to the main loop
    if index > 0 or led:
        #before that, play again what was rewinded
        unrewind_video(rewind_buffer, index)
        continue
    else:
        last_frame = cv2.cvtColor(rewind_buffer[0], cv2.COLOR_BGR2GRAY)
        last_frame = cv2.imwrite('last_frame.jpg',  last_frame)
        rewind_buffer = []
        buffer_speed = 1
        base_time = 0
        frame_count = 0
        old_faces_amount = 0
        led = 1
        mute = 1
        mixer.music.load('deep_time.ogg')
        video.release()
        video = cv2.VideoCapture('deep_time_20fps.mp4')
        fade_out(last_frame, thumb, 60);
        print('Restarted')

webcam.release()
video.release()
cv2.destroyAllWindows()





#TODO create key press callback
