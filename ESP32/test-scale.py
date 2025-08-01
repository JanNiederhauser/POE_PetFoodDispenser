from machine import freq
import time
from hx711test import HX711

freq(160000000)

my_hx711_1 = HX711(4,6)
my_hx711_2 = HX711(4, 15)
my_hx711_2.powerDown()  # Ensure the second HX711 is powered down initially
print("HX711 offset: %.1f" % my_hx711.offset)
my_hx711_1.tare()

count = 0
while True:
    time.sleep(1)
    count += 1
    print("HX711 value %i: %.1f" % (count, my_hx711_2.read()))