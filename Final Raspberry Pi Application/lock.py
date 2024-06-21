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
try:
    set_servo_pulsewidth(500)
    sleep(2)
    set_servo_pulsewidth(2500)
    sleep(2)
finally:
    pi.set_servo_pulsewidth(SERVO_PIN,0)
    pi.stop()
os.system("sudo killall pigpiod")
