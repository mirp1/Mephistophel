#Основной "полный" код.
#Подъем сервы без замедления. Опускание с замедлением
#Подключаем основные библиотеки
from machine import Pin,PWM,I2C
from MX1508 import *
from tcs34725 import *
from servo import Servo
from time import sleep, sleep_ms
from neopixel import NeoPixel
import bluetooth
from ble_simple_peripheral import BLESimplePeripheral
import uasyncio as asio
import math
#Инициализируем моторы
motor_R1 = MX1508(13, 12) 
motor_L1 = MX1508(23, 15)
motor_R2 = MX1508(32, 33)
motor_L2 = MX1508(4, 14)
#Команды для управления
Digital_mode = b'\xff\x00\x02\x01\x02\x01\x01\x00'
Start        = b'\xff\x01\x01\x01\x02\x01\x00\x00' #- may be used for initiating moving
Select       = b'\xff\x01\x01\x01\x02\x02\x00\x00' # Инвалидный датчик
Stop         = b'\xff\x01\x01\x01\x02\x00\x00\x00'
Forward      = b'\xff\x01\x01\x01\x02\x00\x01\x00'
Backward     = b'\xff\x01\x01\x01\x02\x00\x02\x00'
Right        = b'\xff\x01\x01\x01\x02\x00\x08\x00'
Left         = b'\xff\x01\x01\x01\x02\x00\x04\x00'
X            = b'\xff\x01\x01\x01\x02\x10\x00\x00'
O            = b'\xff\x01\x01\x01\x02\x08\x00\x00'
Square       = b'\xff\x01\x01\x01\x02 \x00\x00'
Triangle     = b'\xff\x01\x01\x01\x02\x04\x00\x00'

#Переменные движения
Speed = 500
Sp = 0
Sp_R1=500 #Ощущуение что теперь моторы примерно одинаково работают
#Инициализируем цветодатчик
i2c_bus1 = I2C(0, sda=Pin(21), scl=Pin(22))
tcs = TCS34725(i2c_bus1)
tcs.gain(4)
tcs.integration_time(80)
#Инициализируем светодиод
NUM_OF_LED = 3
np = NeoPixel(Pin(25), NUM_OF_LED)
np[0]=(0,0,0)
Lt=60 #Яркость диода
#Инициализируем сервоприводы
motor_1 = Servo(18)
motor_2 = Servo(26)
#Начальное положение. Я не стала их отдельно устанавливать
#motor_1.move(90)
#motor_2.move(90)

#Переменные серв
#Начальные углы, нужно подобрать
ang_1 = 20
ang_2 = 150
ang_3 = 60
ang_4 = 120
ang_5 = 90
#Шаг в цикле
step = 10
ang = 0
#Инициализируем обмен данными
ble = bluetooth.BLE()
dev = BLESimplePeripheral(ble)
#Общие переменные
debug = 1
int_ms=100

# Сейчас данная функция плавность не обеспечивает. Оставлена для возможности дальнейшей регулировки
# Собственно, сама функция плавности 
#Она постепенно переводит серву от первоначального положения beg_ang к конечному end_ang с шагом step через время t
# Соответственно, сообщаем 5 аргументов, где pwm наше устройство: motor_1 или motor_2
def pulse_1(pwm,beg_ang, end_ang, step, t):
    global ang
    for i in range(0, 100, step):
        # Двигает на постепенно вырастающее выражение, где сначала множетель (pow(i/100, 3) = 0, а в конце 1
        # Тут должна быть подходящая по плавности функция из видоса или наша((pow(i/100, 3)-функция плавности, тут это (i/100)^3)
        # Используемая тут хорошо работала с отдельной сервой
        # для сложных функций нужна math
        pwm.move(int(beg_ang +(end_ang-beg_ang)*(pow(1, 1))))
        sleep_ms(t)
        
# Собственно, сама функция плавности
#Она постепенно переводит серву от первоначального положения beg_ang к конечному end_ang с шагом step через время t
# Соответственно, сообщаем 5 аргументов, где pwm наше устройство: motor_1 или motor_2
def pulse_2(pwm,beg_ang, end_ang, step, t):
    global ang
    for i in range(0, 100, step):
        # Двигает на постепенно вырастающее выражение, где сначала множетель (pow(i/100, 3) = 0, а в конце 1
        # Тут должна быть подходящая по плавности функция из видоса или наша((pow(i/100, 3)-функция плавности, тут это (i/100)^3)
        # Используемая тут хорошо работала с отдельной сервой
        # для сложных функций нужна math
        pwm.move(int(beg_ang +(2*i/100*(end_ang-beg_ang)/(1+(pow(3, -i/100))))+5)) # функция (2*i/100)*(end_ang-beg_ang)/(1+3^(-i/100))
        sleep_ms(t)                                                                # Типо логарифмическая. В проём дописываем слагаемые - калибруем
        
def move(data) :
        global Sp
        global ang_1
        global ang_2
        global ang_3
        global ang_4
        global ang_5
        global step
        global int_ms
        global NUM_OF_LED
        global Lt
        # Запуск без кнопки Start
        Sp = Speed
        
        if data == Stop   :
            motor_R1.stop()
            motor_R2.stop()
            motor_L1.stop()
            motor_L2.stop()
        if data == Forward :
            motor_R1.forward(Sp_R1)
            motor_R2.forward(Sp)
            motor_L1.forward(Sp)
            motor_L2.forward(Sp)
        if data == Backward :
            motor_R1.reverse(Sp_R1)
            motor_R2.reverse(Sp)
            motor_L1.reverse(Sp)
            motor_L2.reverse(Sp)
        if data == Left :
            motor_R1.forward(Sp_R1)
            motor_R2.forward(Sp)
            motor_L1.reverse(Sp)
            motor_L2.reverse(Sp)
        if data == Right :
            motor_R1.reverse(Sp_R1)
            motor_R2.reverse(Sp)
            motor_L1.forward(Sp)
            motor_L2.forward(Sp)
        # Захват    
        if data == X :
            #pulse_1(motor_1, ang_1, ang_2, step, int_ms)
            motor_1.move(ang_1)
        if data == Square :
            #pulse_1(motor_1, ang_2, ang_1, step, int_ms)
            motor_1.move(ang_2)
        # Подъём / опускание манипулятора
        if data == Triangle :
            #pulse_2(motor_2, ang_3, ang_4, step, int_ms) #Замедленный подъём
            motor_2.move(ang_4)
        if data == O :
            #pulse_1(motor_2, ang_4, ang_3, step, int_ms)
            motor_2.move(ang_3)
        # "Режим убийцы" - попытка перевернуть соперника
        if data == Start :
            motor_2.move(ang_5)
            
        # Цветодатчик, работающий по кнопке.
        # Логика кода следующая: МИРП катается, берёт кубики и шарики, предварительно сканируя. На разрешённые цвета реакции светодиода нет
        # Если МИРП найдёт запрещённый цвет, светодиод загорится белым (т.к. свет будет при этом наиболее ярким)
        # Для обеспечения функционирования нужно у запрещённого цвета раскодировать строки #np[0]=(Lt,Lt,Lt) и #np.write()
        if data == Select:
            rgb=tcs.read(1)
            r,g,b=rgb[0],rgb[1],rgb[2]
            h,s,v=rgb_to_hsv(r,g,b)
            if v<99:
                print('Black')
                np[0]=(0,0,0)      # Тот цвет, который нашли. Его же декодируем, если цвет разрещенный
                #np[0]=(Lt,Lt,Lt)   # Белый цвет, горит при опасности
                np.write()         # Светодиод, включается при опасности
                
            elif 100<v<999:
                if 0<h<40:
                    # Выполняет роль запрещённого цвета
                    print('Red')
                    np[0]=(Lt,0,0)      # Тот цвет, который нашли
                    #np[0]=(Lt,Lt,Lt)    # Белый цвет, горит при опасности
                    #np[0]=(0,0,0)      # Светодиод не горит, цвет разрешен
                    np.write()          # Светодиод, включается при опасности
                    
                elif 41<h<120:
                    print('Yellow')
                    np[0]=(Lt,Lt,0)     # Тот цвет, который нашли
                    #np[0]=(Lt,Lt,Lt)    # Белый цвет, горит при опасности
                    #np[0]=(0,0,0)       # Светодиод не горит, цвет разрешен
                    np.write()          # Светодиод, включается при опасности
                    
                elif 121<h<160:
                    print('Green')
                    np[0]=(0,Lt,0)     # Тот цвет, который нашли
                    #np[0]=(Lt,Lt,Lt)   # Белый цвет, горит при опасности
                    #np[0]=(0,0,0)      # Светодиод не горит, цвет разрешен
                    np.write()         # Светодиод, включается при опасности
                    
                elif 160<h<210:
                    print('Cyan')
                    np[0]=(0,Lt,Lt)     # Тот цвет, который нашли
                    #np[0]=(Lt,Lt,Lt)    # Белый цвет, горит при опасности
                    #np[0]=(0,0,0)       # Светодиод не горит, цвет разрешен
                    np.write()          # Светодиод, включается при опасности
                    
                elif 211<h<240:
                    print('Blue')
                    np[0]=(0,0,Lt)     # Тот цвет, который нашли
                    #np[0]=(Lt,Lt,Lt)   # Белый цвет, горит при опасности
                    #np[0]=(0,0,0)      # Светодиод не горит, цвет разрешен
                    np.write()         # Светодиод, включается при опасности
                    
                elif 241<h<300:
                    print('Magenta')
                    np[0]=(Lt,0,Lt)     # Тот цвет, который нашли
                    #np[0]=(Lt,Lt,Lt)    # Белый цвет, горит при опасности
                    #np[0]=(0,0,0)       # Светодиод не горит, цвет разрешен
                    np.write()          # Светодиод, включается при опасности
                    
            elif v>1000:
                print('White')
                #np[0]=(Lt,Lt,Lt)   # Белый цвет, его нашли
                np[0]=(0,0,0)      # Светодиод не горит, цвет разрешен
                np.write()         # Светодиод, включается при опасности
                
           # if debug:
           # print('Color is {}. R:{} G:{} B:{} H:{:.0f} S:{:.0f} V:{:.0f}'.format([col_id],r,g,b,h,s,v))
            
        if debug == 1:
            print("Data received: ", data)  # Print the received data
        
        
            
async def exchange(int_ms) :
    while 1 :
        if dev.is_connected(): # Check if a BLE connection is established
            dev.on_write(move)
        await asio.sleep_ms(int_ms)
      

loop = asio.get_event_loop()
loop.create_task(exchange(1))
#loop.create_task(color_det())
loop.run_forever()

