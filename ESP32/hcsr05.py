import time
from machine import Pin

class DistanceSensor:
    """
    A class to interface with an HC-SR05 ultrasonic distance sensor using an ESP32.
    Attributes:
        TRIG (Pin): The GPIO pin configured as the trigger output.
        ECHO (Pin): The GPIO pin configured as the echo input.
    Methods:
        __init__(trig_pin, echo_pin):
            Initializes the DistanceSensor with the specified trigger and echo pins.
        measure_distance():
            Measures the distance to an object using the ultrasonic sensor.
            Returns:
                float: The measured distance in centimeters, rounded to 2 decimal places.
        cleanup():
            Placeholder method for cleanup operations (not required for ESP32 GPIO pins).
    """
    def __init__(self, trig_pin, echo_pin):
        self.TRIG = Pin(trig_pin, Pin.OUT)
        self.ECHO = Pin(echo_pin, Pin.IN)

        # Ensure that the Trigger pin is set low
        self.TRIG.value(0)

        # Allow the sensor to settle
        time.sleep(2)

    def measure_distance(self):
        # Create trigger pulse and set to high
        self.TRIG.value(1)
        time.sleep_us(10)  # For 10 microseconds
        self.TRIG.value(0)

        # Wait for the echo pin to go high and record the start time
        while self.ECHO.value() == 0:
            pulse_start = time.ticks_us()

        # Wait for the echo pin to go low and record the end time
        while self.ECHO.value() == 1:
            pulse_end = time.ticks_us()

        # Calculate the duration of the pulse
        pulse_duration = time.ticks_diff(pulse_end, pulse_start)

        # Calculate the distance in cm
        # Speed of sound is 34300 cm/s, divide by 2 for round trip
        distance = pulse_duration * 0.0343 / 2
        distance = round(distance, 2)  # Round the distance to 2 decimal places

        return distance

    def cleanup(self):
        # No cleanup required for ESP32 GPIO pins
        pass
