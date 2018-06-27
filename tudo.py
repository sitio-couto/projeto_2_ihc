from pygame import mixer
from time import sleep
import cv2, serial

__FACES__ = -1 # Debugging: Fixa numero de faces (-1 desativa)
__LEDRG__ = 0 # Debugging: Fixa valor do led (1-verde, 0-vermelho)

##### MAPPINGS ####################
def visual_files(x):
    return {'image':'thumbnail.png',
            'video':'deep_time_20fps.mp4'
            }.get(x, 0)

def speed_data(x):
    return {1:['deep_time_v2.ogg',1,43,7],
            2:['deep_time_x12_v2.ogg',1.2,32,30],
            3:['deep_time_x14_v2.ogg',1.4,31,30],
            4:['deep_time_x16_v2.ogg',1.6,20,30],
            }.get(x, ['deep_time_x16.ogg',1.6,20,30])
### GLOBAL CONSTANTS ##############
MAX_REWIND = 300    # Max frames in rewind buffer
MAX_OFFSET = 0.1   # MARGEN DE ERRO PARA O AUDIO
TOTAL_FRAMES = 9066 # TOTAL DE FRAMES NO VIDEO
AUDIO_LENGTH_X1 = 453 # DURACAO (EM SEGUNDOS NA VELOLOCIDADE x1) DO AUDIO
FRAME_DELAY = 2    # ATRASO PADRAO ENTRE FRAMES
SCAN_FACES = 3      # PERIODO EM QUE SE EXECUTA O CASCADE
### GLOBAlS #######################
def glb():
    glb.led = 0             # VALOR DO LED
    glb.old_led = 0         # VALOR ANTERIOR DO LED (checkar se mudou de estado)
    glb.faces_amount = 0
    glb.old_faces_amount = 0 # NUMER DE FACES ANTES DE ATUALIZAR
    glb.frame_count = 0      # FRAME ATUAL
    glb.base_time = 0        # TEMPO DE REFERECIA (necessario devido ao get_pos() da pygame)
    glb.update_count = -1  # CONTA FRAMES ATE ATUAIZAR O CASCADE
################################################################################

def find_faces(webcam):
    global __FACES__

    try:
        ret, image = webcam.read() #capture from webcam
    except:
        print("Something went wrong")
        exit(0)
    grayscaled_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)      # to greyscale
    faces = face_cascade.detectMultiScale(grayscaled_image, 1.3, 5) # find faces in the image

    if __FACES__ < 0: return len(faces) # return faces quantity
    else: return __FACES__  # if debugger set

### REWINDS VIDEO ###
def rewind_video(rewind_buffer, webcam, index):
    mixer.music.stop() # stops audio playback

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

# TODO
### CONDITION WICH DETERMINS IF THERE ARE PEOPLE ###
def theres_people(): return (glb.faces_amount or glb.led)

### PLAY VIDEO FORWARD ###
def play_video(rewind_buffer):
    while theres_people():
        ret, frame = video.read()   # get next frame
        rewind_buffer.append(frame) # updates video buffer

        if len(rewind_buffer) >= MAX_REWIND: # check buffers for max capacity
            rewind_buffer.pop(0)

        update_playback_data(); # Updates faces, LED and audio speed
        display_frame(frame)    # Show frame

        if (glb.frame_count == TOTAL_FRAMES):
            return 'ending', 0

    return 'rewind', (len(rewind_buffer) - 1)

### UPDATE AUDIO SPEED ACCORDING TO THE LED AND FACES ###
def update_playback_data():
    glb.update_count += 1

    if (glb.update_count % speed_data(glb.faces_amount)[3]) == 0:
        glb.led = led_status()
        glb.faces_amount = find_faces(webcam)

        if not (glb.faces_amount == glb.old_faces_amount) or not (glb.led == glb.old_led):
            if (glb.faces_amount): # Se ha mais que 0 faces
                mixer.music.load(speed_data(glb.faces_amount)[0])
            elif (glb.led): # Se ha 0 faces mas o led esta verde
                mixer.music.load(speed_data(1)[0]) # Carrega audio de velo x1
            glb.base_time = get_audio_checkpoint() # Salva o tempo esperado do frame
            mixer.music.play(0, glb.base_time)
            glb.old_faces_amount = glb.faces_amount
            glb.old_led = glb.led
        
    return

# ### DEFINE AS CONDICOES EM QUE O AUDIO DEVE SER ATUALIZADO ###
# # As condicionais garantem o audio seja sincronizado apenas em momentos
# # necessarios, deixando o audio mais fluido. Deveria ir na linha 120
# # na condicao do segundo if, mas nao terminei de testar.
# def update_conditions(faces_amount, old_faces_amount, led, old_led):
#     # Muda velocidade (de [0:n] para [1:n], nao muda para zero)
#     a = not (old_faces_amount == faces_amount) and (faces_amount >= 1)
#     # resume ao video (esta em rewinding e deve voltar ao video)
#     b = not (old_led or old_faces_amount) and (faces_amount or led)
#     # No caso de haver uma mudanca simultanea de valores (sensor ativa, camera desativa)
#     c = (not old_led) and led and (not old_faces_amount) and faces_amount
#      # No caso de haver uma mudanca simultanea de valores (sensor desativa, camera ativa)
#     d = old_led and (not led) and old_faces_amount and (not faces_amount)
#
#     return a or b or c or d

### REPLAYS FRAMES ###
def replay_frame(frame):
    glb.frame_count -= 1 # Decrementa frame retrocedido
    gray = cv2.cvtColor(add_observers(frame), cv2.COLOR_BGR2GRAY)  # to greyscale
    cv2.imshow('frame', gray)     # show the frame frame
    cv2.waitKey(speed_data(1)[2]) # Velocidade de rewind e irrelevante, usa a de x1
    return

### SHOW NEW FRAMES ###
def display_frame(frame):
    glb.frame_count += 1    # Incrementa o frame a ser mostrado
    cv2.imshow('frame', add_observers(frame))    # show the frame frame
    cv2.waitKey(sync_video())  # sync_video adia ou atrasa o frame se necessario
    return

### ADDS OBSERVERS INDICATOR TO THE FRAME ###
def add_observers(frame):
    frame_copy = frame.copy()   # Cria deep copy do frame

    # Verifica numero de obseradores e a velicidade
    if (glb.faces_amount):
        observers = glb.faces_amount
        speed = speed_data(glb.faces_amount)[1]
    elif (glb.led): # Caso nao haja faces mas o led esteja aceso
        observers = 1
        speed = 1 # se for apenas o led, velo e sempre 1
    else:
        observers = 0
        speed = -1

    # Acreseta o texto a deep copy do frame, evitando que o frame original seja afetado
    text  = "OBSERVERS: " + str(observers) + " (x" + str(speed) + ")"
    cv2.putText(frame_copy, text, (10,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0))

    return frame_copy # Retrona a deep copy com o texto adicionado

### UPDATES LED STATUS READING SERIAL PORT ###
def led_status():
    global arduino, __LEDRG__
    if (__LEDRG__ >= 0): return __LEDRG__ # if debugger is set

    if arduino.in_waiting:                         # Se houver novas entradas
        serial_in = arduino.read(arduino.in_waiting) # Le todas as novas entradas

    return serial_in[-1]       # Retorna a entrada mais recente

### SYNCS VIDEO WITH THE EXPECTED AUDIO TIME ###
def sync_video():
    global MAX_OFFSET

    delay = speed_data(glb.faces_amount)[2] # seta o delay como o padrao para a velocidade atual
    offset = get_audio_time() - get_audio_checkpoint() # Pega diferenca entre a posicao atual do audio, e a posicao
                                                       # esperada do audio para o frame atual (time - checkpoint)
    # mostra o delay (serve para regular DELAY e FACES, deixando o video mais fluido)
    if abs(offset) > MAX_OFFSET:
        print('SYNC|x',speed_data(glb.faces_amount)[1],'| frame: ', glb.frame_count,' | offset:',offset)

    # Verifica se o atraso excede a margem de erro MAX_OFFSET
    if offset < -(MAX_OFFSET):
        sleep(abs(offset)) # Se atrasado, segura o video para alcaca-lo
    elif offset > MAX_OFFSET:
        delay = 1          # Se adiantado, acelera o video sobreescrevendo o delay para 1 (minimo)

    return delay

### GETS EXPECTED AUDIO TIME ###
## WARNING: PARA COLOCAR OUTRO VIDEO DEVE-SE MUDAR AUDIO_LENGTH_X1 E TOTAL_FRAMES
# Calcula a duracao do audio na velocidade atual e retorna a posicao esperada
# do audio (segundos) e retorna.
def get_audio_checkpoint():
    global TOTAL_FRAMES, AUDIO_LENGTH_X1
    audio_length = AUDIO_LENGTH_X1/speed_data(glb.faces_amount)[1]
    return (glb.frame_count*audio_length/TOTAL_FRAMES)

### GETS CURRENTE AUDIO TIME ###
# recupera o tempo desde o comando mixer.music.play() e acresenta basetime
# obtendo a posica atual do audio. Como os comandos mixer.music.play()
# mixer.music.stop() resetam o tempo, usa o base-time para ajustar o valor
def get_audio_time():
    return (mixer.music.get_pos()/1000) + glb.base_time

### ADDS FADE EFFECT FROM img1 TO img2 ###
def fade_out (img1, img2, len=10): #pass images here to fade between
    for IN in range(0,len):
        fadein = IN/float(len)
        dst = cv2.addWeighted(img1, 1-fadein, img2, fadein, 0)
        cv2.imshow('frame', dst)
        cv2.waitKey(1)

### BOOT UP ####################################################################

def boot_functions():
    # Create 'frame' window and configure for fullscreen
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL);
    cv2.setWindowProperty('frame', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
    # Open cascade and webcam
    face_cascade = cv2.CascadeClassifier("cascade_face.xml") # Open the Haar Cascade
    webcam = cv2.VideoCapture(0) # Open webcam
    # Open serial port (if __LEDRG__ >= 0) and mixer
    if (__LEDRG__ < 0): arduino = serial.Serial('COM3', 115200)
    else: arduino = 0
    mixer.init()

    # Wait for things to actually open
    while not webcam.isOpened() and not (arduino.is_open or __LEDRG__ < 0):
        continue

    print('BOOTED UP')
    return face_cascade, webcam, arduino

def load_midia():
    mixer.music.load(speed_data(1)[0])
    video = cv2.VideoCapture(visual_files('video')) # Open video

    while not video.isOpened(): continue

    print('Midia files set')
    return video

################################################################################
### MAIN LOOP ##################################################################

face_cascade, webcam, arduino = boot_functions(); # Open stuff
video = load_midia() # Load video and music

# Setup thumbnail and first_frame
thumb = cv2.imread(visual_files('image'), cv2.IMREAD_COLOR)
ret, first_frame = video.read()

glb() # initialize globals
current_state = 'start' # Estado do video
rewind_buffer = []  # Buffer de frames
index = 0   # indice para navegar pelo rewind buffer

while True:
    print(current_state)

    if current_state == 'start':
        cv2.imshow('frame', thumb) # Mostra a thumbnail estatica
        cv2.waitKey(1)

        while not theres_people(): # Aguarda observadores
            glb.led = led_status();
            glb.faces_amount = find_faces(webcam)
            sleep(0.3)

        mixer.music.play()
        fade_out(thumb, first_frame, 30); # Fadeout from thumb to first_frame
        current_state = 'play'

    elif current_state == 'play': # Play the video while there are faces, or led
        current_state, index = play_video(rewind_buffer)

    elif current_state == 'rewind': # if the faces disappear, rewind video
        current_state, index = rewind_video(rewind_buffer, webcam, index)

    elif current_state == 'unrewind': # play what was rewinded
        current_state, index = unrewind_video(rewind_buffer, index)

    elif current_state == 'restart': # Reinicia variaveis, video e audio
        if (rewind_buffer): last_frame = rewind_buffer[0]
        else: last_frame = frame_first
        fade_out(last_frame, thumb, 60); # Fades from last frame shown to thumb
        mixer.music.stop()
        video.release()
        video = load_midia()
        rewind_buffer = []
        index = 0
        glb()
        current_state = 'start'

webcam.release()
video.release()
cv2.destroyAllWindows()
