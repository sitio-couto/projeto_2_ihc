import serial

port = 'COM3'
baudrate = 115200

ser = serial.Serial(port, baudrate)

while True:

    while not ser.is_open: ser.open()

    while ser.is_open:
        if (ser.in_waiting):
            input = ser.read(ser.in_waiting)

            if input[-1]:
                print("LUZ VERDE!!!")
            else:
                print("LUZ VERMELHA!!!")
