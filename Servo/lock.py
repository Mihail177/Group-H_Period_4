import pigpio
import os
from time import sleep

os.system("sudo pigpiod")
sleep(1)

pi = pigpio.pi()
if not pi.connected:
    print("not connected")
    exit()
SERVO_PIN = 18
def set_servo_pulsewidth(pulsewidth):
    pi.set_servo_pulsewidth(SERVO_PIN,pulsewidth)

# set_servo_pulsewidth(2500)
# sleep(2)


try:
    print("setting servo to mid pos")
    set_servo_pulsewidth(1500)
    sleep(2)
    print("setting servo to min pos")
    set_servo_pulsewidth(500)
    sleep(2)
    print("set servo to maximum pos")
    set_servo_pulsewidth(2500)
    sleep(2)
finally:
    pi.set_servo_pulsewidth(SERVO_PIN,0)
    pi.stop()
os.system("sudo killall pigpiod")
