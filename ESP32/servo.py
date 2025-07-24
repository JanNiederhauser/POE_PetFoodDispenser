from machine import Pin, PWM
import time


class Servo:
    def __init__(self, pin):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(50)  # 50 Hz = 20 ms period

    def move_us(self, us):
        """Set pulse width in microseconds (us), e.g. 1000–2000"""
        self.pwm.duty_ns(us * 1000)  # Convert to nanoseconds

    def left(self):
        self.move_us(1000)  # 1 ms pulse
        time.sleep(0.5)

    def center(self):
        self.move_us(1500)  # 1.5 ms pulse
        time.sleep(0.5)

    def right(self):
        self.move_us(2000)  # 2 ms pulse
        time.sleep(0.5)
