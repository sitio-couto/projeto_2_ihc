from pygame import mixer
from time import sleep
import cv2, serial

__FACES__ = -1 # Debugging: Fixa numero de faces (-1 desativa)
__LEDRG__ = 0 # Debugging: Fixa valor do led (1-verde, 0-vermelho)

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
    else: return __FACES__  # if debugger set


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
        mixer.music.load('deep_time_x12_v2.ogg')
    elif faces_amount == 3:
        VIDEO_DELAY = 31
        SCAN_FACES = 30
        multiplier = buffer_speed/1.4
        buffer_speed = 1.4
        audio_length = 323
        mixer.music.load('deep_time_x14_v2.ogg')
    else:
        VIDEO_DELAY = 20
        SCAN_FACES = 30
        multiplier = buffer_speed/1.6
        buffer_speed = 1.6
        audio_length = 283
        mixer.music.load('deep_time_x16_v2.ogg')

    base_time = get_audio_checkpoint()

    return base_time

### REWINDS VIDEO ###
def rewind_video(rewind_buffer, webcam, index):
    global buffer_speed

    mixer.music.stop() # stops audio playback
    buffer_speed = -1  # Atualiza velocidade do buffer

    # Pega segunda metade do buffer (porcao que foi rewinded)
    for i, frame in enumerate(reversed(rewind_buffer[ :index])):
        replay_frame(frame)
        update_playback_data()          # Verifica atualizacao de velocidade
        if theres_people():             # Se apareceu observers
            return 'unrewind', (index - i) # Retorna estado e posicao do buffer

    return 'restart', 0   # If surpasses buffer length, resets

### REPLAYS WHAT WAS REWINDED ###
def unrewind_video(rewind_buffer, index):
    # Mostra frames do buffer novamente
    for i, frame in enumerate(rewind_buffer[index: ]):
        update_playback_data();
        display_frame(frame)
        if not theres_people():
            return 'rewind', (index + i)

    return 'play', 0 # Resume playing unchached frames

### CONDITION WICH DETERMINS IF THERE ARE PEOPLE ###
def theres_people():
    global faces_amount, led
    return (faces_amount > 0 or led)

### PLAY VIDEO FORWARD ###
def play_video(rewind_buffer, frame_count):
    global faces_amount

    while (faces_amount > 0 or led):
        ret, frame = video.read()   # get next frame
        rewind_buffer.append(frame) # updates video buffer

        # check buffers for max capacity
        if len(rewind_buffer) >= MAX_REWIND:
            rewind_buffer.pop(0)

        update_playback_data(); # Updates faces, LED and audio speed
        display_frame(frame)    # Show frame

        if (frame_count == TOTAL_FRAMES):
            return 'ending', 0

    return 'rewind', (len(rewind_buffer) - 1)

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
# As condicionais garantem o audio seja sincronizado apenas em momentos
# necessarios, deixando o audio mais fluido
def update_conditions(faces_amount, old_faces_amount, led, old_led):
    # Muda velocidade (de [0:n] para [1:n], nao muda para zero)
    a = not (old_faces_amount == faces_amount) and (faces_amount >= 1)
    # resume ao video (esta em rewinding e deve voltar ao video)
    b = not (old_led or old_faces_amount) and (faces_amount or led)
    # No caso de haver uma mudanca simultanea de valores (sensor ativa, camera desativa)
    c = (not old_led) and led and (not old_faces_amount) and faces_amount
     # No caso de haver uma mudanca simultanea de valores (sensor desativa, camera ativa)
    d = old_led and (not led) and old_faces_amount and (not faces_amount)

    return a or b or c or d

### REPLAYS FRAMES ###
def replay_frame(frame):
    global DELAY, frame_count

    frame_count -= 1 # Decrementa frame retrocedido
    gray = cv2.cvtColor(add_observers(frame), cv2.COLOR_BGR2GRAY)  # to greyscale
    cv2.imshow('frame', gray)        # show the frame frame
    cv2.waitKey(DELAY)               # wait for delay
    return

### SHOW NEW FRAMES ###
def display_frame(frame):
    global DELAY, frame_count

    sync_video()        # Adia ou atrasa o frame se necessario
    frame_count += 1    # Incrementa o frame a ser mostrado
    cv2.imshow('frame', add_observers(frame))    # show the frame frame
    cv2.waitKey(DELAY)                           # wait for DELAY
    return

### ADDS OBSERVERS INDICATOR TO THE FRAME ###
def add_observers(frame):
    global faces_amount, buffer_speed

    frame_copy = frame.copy()   # Cria deep copy do frame

    if buffer_speed > 0 and faces_amount == 0:
        observers = 1   # Caso nao haja faces mas o led esteja ativo, mostra 1 observador
    else:
        observers = faces_amount

    # Acreseta o texto a deep copy do frame, evitando que o frame original seja afetado
    text = "OBSERVERS: " + str(observers) + " (x" + str(float(buffer_speed)) + ")"
    cv2.putText(frame_copy, text, (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0))

    return frame_copy # Retrona a deep copy com o texto adicionado

### UPDATES LED STATUS READING SERIAL PORT ###
def led_status():
    global board, serial_in, __LEDRG__
    if (__LEDRG__ >= 0): return __LEDRG__ # if debugger is set

    if board.in_waiting:                         # Se houver novas entradas
        serial_in = board.read(board.in_waiting) # Le todas as novas entradas

    return serial_in[-1]       # Retorna a entrada mais recente

### SYNCS VIDEO WITH THE EXPECTED AUDIO TIME ###
def sync_video():
    global AUDIO_DELAY, VIDEO_DELAY, DELAY, buffer_speed

    DELAY = VIDEO_DELAY # seta o delay como o padrao para a velocidade atual
    delay = get_audio_time() - get_audio_checkpoint()   # Pega diferenca entre a posicao atual do audio, e a posicao
                                                        # esperada do audio para o frame atual (time - checkpoint)

    # mostra o delay (serve para regular VIDEO_DELAY e SCAN_FACES, deixando o video mais fluido)
    if abs(delay) > AUDIO_DELAY:
        print('SYNC|x',buffer_speed,'| frame: ',frame_count,' | delay:',delay)

    # Verifica se o atraso excede a margem de erro AUDIO_DELAY
    if delay < -(AUDIO_DELAY):
        sleep(abs(delay))   # Se atrasado, segura o video para alcaca-lo
    elif delay > AUDIO_DELAY:
        DELAY = 1           # Se adiantado, acelera o video sobreescrevendo o DELAY para 1 (minimo)

    return

### GETS EXPECTED AUDIO TIME ###
## WARNING: PARA COLOCAR OUTRO VIDEO DEVE-SE MUDAR audio_length E total_frames
def get_audio_checkpoint():
    global frame_count, audio_length, TOTAL_FRAMES
    return (frame_count*audio_length/TOTAL_FRAMES)

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

def boot_functions():
    # Create 'frame' window and configure for fullscreen
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL);
    cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
    # Open cascade and webcam
    face_cascade = cv2.CascadeClassifier("cascade_face.xml") # Open the Haar Cascade
    webcam = cv2.VideoCapture(0) # Open webcam
    # Open serial port (if __LEDRG__ >= 0) and mixer
    if (__LEDRG__ < 0): board = serial.Serial('COM3', 115200)
    mixer.init()

    # Wait for things to actually open
    while not webcam.isOpened() and not (board.is_open or __LEDRG__ < 0):
        continue

    print('BOOTED UP')
    return face_cascade, webcam

def load_midia():
    mixer.music.load('deep_time.ogg')
    video = cv2.VideoCapture('deep_time_20fps.mp4') # Open video

    while not video.isOpened(): continue

    print('Midia files set')
    return video

# Globals
MAX_REWIND = 300    # Max frames in rewind buffer
VIDEO_DELAY = 43    # ATRASO PADRAO ENRRE FRAMES
AUDIO_DELAY = 0.1   # MARGEN DE ERRO PARA O AUDIO
DELAY = 43          # ATRASO ALTERADO PARA SINCRNIZAR
SCAN_FACES = 7      # PERIODO EM QUE SE EXECUTA O CASCADE
TOTAL_FRAMES = 9066 # TOTAL DE FRAMES NO VIDEO
serial_in = [0]     # BUFFER PARA A PORTA SERIAL
led = 0             # VALOR DO LED
old_led = 0         # VALOR ANTERIOR DO LED (checkar se mudou de estado)

rewind_buffer = []
faces_amount = 0
old_faces_amount = 0 # NUMER DE FACES ANTES DE ATUALIZAR
frame_count = 0      # FRAME ATUAL
index = 0            # INDEX PARA OSCILAR NO rewind_buffer

audio_length = 453   # TEMPO (SEGUNDOS) DA FAIXA DE AUDIO
buffer_speed = 1     # VELOCIDADE ATUAL DO VIDEO
base_time = 0        # TEMPO DE REFERECIA (necessario devido ao get_pos() da pygame)
update_cont = 0      # CONTADOR QUE INDICA QUANDO DEVE-SE EXECUTAR O CASCADE (junto com o SCAN_FACES)

start_flag = 1       # FLAG PARA HABILITAR O FADE_OUT DO INICO DO VIDEO
end_flag = 0         # FLAG PARA PULAR rewind E unrewind E ENCERAR O VIDEO

visual_files = {1:'thumbnail.png',2:'deep_time_20fps'}
audio_files = {}


################################################################################

face_cascade, webcam = boot_functions(); # Open stuff
video = load_midia() # Load video and music

thumb = cv2.imread('thumbnail.png', cv2.IMREAD_COLOR)
ret, first_frame = video.read()
first_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

current_state = 'start'
index = 0

while True:
    print(current_state)

    # Aguarda ate que a flag seja setada
    while current_state == 'start':
        # Mostra a thumbnail estatica
        cv2.imshow('frame', thumb)
        cv2.waitKey(1)
        # atualiza o led e o cascade
        led = led_status();
        faces_amount = find_faces(webcam)
        # Comeca ou dorme
        if (faces_amount > 0 or led):
            current_state = 'play'
            fade_out(thumb, first_frame, 30); # Fadeout from thumb to first_frame
        else:
            sleep(0.2)

    if current_state == 'play':
        # Play the video while there are faces, or led
        current_state, index = play_video(rewind_buffer, frame_count)

    elif current_state == 'rewind':
        # if the faces disappear, rewind video
        current_state, index = rewind_video(rewind_buffer, webcam, index)

    elif current_state == 'unrewind':
        #before that, play again what was rewinded
        current_state, index = unrewind_video(rewind_buffer, index)

    elif current_state == 'restart':
        if rewind_buffer:
            last_frame = cv2.cvtColor(rewind_buffer[0], cv2.COLOR_BGR2GRAY)
        else:
            last_frame = frame_first

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
        video.release()
        video = load_midia()
        fade_out(last_frame, thumb, 60);
        current_state = 'start'

webcam.release()
video.release()
cv2.destroyAllWindows()





#TODO create key press callback
