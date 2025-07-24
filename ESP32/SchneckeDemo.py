from machine import Pin, PWM
import time

# PWM mit 50Hz auf GPIO 7 (Pin D7)
servo = PWM(Pin(7))
servo.freq(50)


def move_snail():
    pwm = PWM(Pin(7))
    pwm.freq(50)
    pwm.duty(105)
    time.sleep(0.2)
    pwm.deinit()

move_snail()
