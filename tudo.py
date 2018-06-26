from pygame import mixer
from time import sleep
import cv2, serial


__FACES__ = -1
__LEDRG__ = -1

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

    if faces_amount == 1 or faces_amount == 0:
        VIDEO_DELAY = 43
        SCAN_FACES = 7
        multiplier = buffer_speed/1
        buffer_speed = 1
        audio_length = 453
        mixer.music.load('deep_time_v2.ogg')
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

### REWINDS VIDEO ###
def rewind_video(rewind_buffer, webcam):
    global buffer_speed, index, faces_amount, led
    print("Rewinding")

    mixer.music.stop() # stops audio playback
    buffer_speed = -1

    for i in range(len(rewind_buffer)-1, -1, -1):
        index += 1
        replay_frame(rewind_buffer[i])
        update_playback_data()
        if theres_people(): return index

    return -1       # If surpasses buffer length, return to FRAME_0

### REPLAYS WHAT WAS REWINDED ###
def unrewind_video(rewind_buffer):
    global index
    print("Unrewinding")

    for frame in rewind_buffer[len(rewind_buffer)-index:]:
        index -= 1
        update_playback_data();
        display_frame(frame)
        if not theres_people(): break

    return

### CONDITION WICH DETERMINS IF THERE ARE PEOPLE ###
def theres_people():
    global faces_amount, led
    return (faces_amount > 0 or led)

### PLAY VIDEO FORWARD ###
def play_video(rewind_buffer, video, faces_amount):

    ret, frame = video.read()   # get next frame
    rewind_buffer.append(frame) # updates video buffer

    # check buffers for max capacity
    if len(rewind_buffer) >= MAX_REWIND:
        rewind_buffer.pop(0)

    update_playback_data(); # Updates faces, LED and audio speed
    display_frame(frame)    # Show frame
    return

### UPDATE AUDIO SPEED ACCORDING TO THE LED AND FACES ###
def update_playback_data():
    global SCAN_FACES, update_cont, old_led, led, old_faces_amount, faces_amount
    update_cont += 1

    if (update_cont % SCAN_FACES) == 0:
        led = led_status()
        faces_amount = find_faces(webcam)

        if  not (old_faces_amount == faces_amount) or not (led == old_led):
            mixer.music.play(0, audio_speed(faces_amount))
            old_faces_amount = faces_amount
            old_led = led

    return # Returns 1 if updates

### DEFINE AS CONDICOES EM QUE O AUDIO DEVE SER ATUALIZADO ###
def update_conditions(faces_amount, old_faces_amount, led, old_led):
    a = not (old_faces_amount == faces_amount) and (faces_amount >= 1) # Muda velocidade
    b = not (old_led or old_faces_amount) and (faces_amount or led)   # resume ao video
    c = (not old_led) and led and (not old_faces_amount) and (faces_amount)   # resume ao video
    d = old_led and (not led) and old_faces_amount and (not faces_amount)
    return a or b or c or d

### REPLAYS FRAMES ###
def replay_frame(frame):
    global DELAY, frame_count

    frame_count -= 1
    gray = cv2.cvtColor(add_observers(frame), cv2.COLOR_BGR2GRAY)  # to greyscale
    cv2.imshow('frame', gray)                        # show the frame frame
    cv2.waitKey(DELAY)               # wait for 25ms
    return

### SHOW NEW FRAMES ###
def display_frame(frame):
    global DELAY, frame_count

    sync_video()
    frame_count += 1
    cv2.imshow('frame', add_observers(frame))    # show the frame frame
    cv2.waitKey(DELAY)                           # wait for DELAY
    return

### ADDS OBSERVERS INDICATOR TO THE FRAME ###
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

### UPDATES LED STATUS READING SERIAL PORT ###
def led_status():
    global board, serial_in, __LEDRG__

    if board.in_waiting:                      # Se houver novas entradas
        serial_in = board.read(board.in_waiting) # Le todas as novas entradas

    if __LEDRG__ < 0: return serial_in[-1]       # Retorna cor mais recente do led
    else: return __LEDRG__

### SYNCS VIDEO WITH THE EXPECTED AUDIO TIME ###
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

### GETS EXPECTED AUDIO TIME ###
def get_audio_checkpoint():
    global frame_count, audio_length
    return (frame_count*audio_length/9066)

### GETS CURRENTE AUDIO TIME ###
def get_audio_time():
    global base_time
    return (mixer.music.get_pos()/1000) + base_time

### ADDS FADE EFFECT FROM img1 TO img2 ###
def fade_out (img1, img2, len=10): #pass images here to fade between
    for IN in range(0,len):
        fadein = IN/float(len)
        dst = cv2.addWeighted(img1, 1-fadein, img2, fadein, 0)
        cv2.imshow('frame', dst)
        cv2.waitKey(1)

################################################################################

cv2.namedWindow('frame', cv2.WINDOW_NORMAL);
cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
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
serial_in = [0]
led = 0
old_led = 0

rewind_buffer = []
faces_amount = 0
old_faces_amount = 0
frame_count = 0
index = 0

# Guarda o momento do audio correspondente ao frame do buffer
audio_length = 453
buffer_speed = 1
base_time = 0
update_cont = 0

start_flag = 1
end_flag = 0

# Inicializa modulo e carrega arquivo de som
mixer.init()
mixer.music.load('deep_time.ogg')

# wait for things to actually open
while not webcam.isOpened() and not video.isOpened() and board.is_open:
    continue

while True:
    print('Main loop')
    # Until find faces or led is green
    while start_flag and faces_amount <= 0 and not led:
        cv2.imshow('frame', thumb)
        cv2.waitKey(1)
        led = led_status();
        faces_amount = find_faces(webcam)
        if (faces_amount > 0 or led):
            print('Starting')
            start_flag = 0
            fade_out(thumb, frame_0, 30);
        else: sleep(0.2)

    # Play the video while there are faces
    while (faces_amount > 0 or led):
        play_video(rewind_buffer, video, faces_amount)
        if frame_count == 9066:
            end_flag = 1
            break

    # if the faces disappear, rewind video
    if not end_flag:
        index = rewind_video(rewind_buffer, webcam)

    # When we run out of buffer go back to the main loop
    if index > 0 and not end_flag:
        #before that, play again what was rewinded
        unrewind_video(rewind_buffer)
        continue
    else:
        if rewind_buffer:
            last_frame = cv2.cvtColor(rewind_buffer[0], cv2.COLOR_BGR2GRAY)
        else:
            last_frame = frame_0
        last_frame = cv2.imwrite('last_frame.jpg',  last_frame)
        rewind_buffer = []
        buffer_speed = 1
        base_time = 0
        frame_count = 0
        old_faces_amount = 0
        led = 0
        old_led = 0
        index = 0
        start_flag = 1
        end_flag = 0
        mute = 1
        mixer.music.stop()
        mixer.music.load('deep_time.ogg')
        video.release()
        video = cv2.VideoCapture('deep_time_20fps.mp4')
        last_frame = cv2.imread('last_frame.jpg', cv2.IMREAD_COLOR)
        fade_out(last_frame, thumb, 60);
        print('Restarted')

webcam.release()
video.release()
cv2.destroyAllWindows()





#TODO create key press callback
