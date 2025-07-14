# dispenser_main.py - Pet Food Dispenser Controller for ESP32-C6 (MicroPython)

import machine
import time
import urequests
from machine import Pin, PWM
from mfrc522 import MFRC522
from hcsr04 import HCSR04
from hx711 import HX711

# --- CONFIGURATION ---
API_BASE = "http://your.backend/api"
SERVO_ENTRY_LOCK_PIN = 6    # GPIO6 - Entry servo
SERVO_PLATE1_LOCK_PIN = 7   # GPIO7 - Lock plate 1 (CD-ROM or servo)
SERVO_PLATE2_LOCK_PIN = 8   # GPIO8 - Lock plate 2 (CD-ROM or servo)
SCHNECKE1_PIN = 10          # GPIO10 - Motor to dispense food (silo 1)
SCHNECKE2_PIN = 11          # GPIO11 - Motor to dispense food (silo 2)

# HX711 pins
HX_ENTRY_DT = 4             # Eingangs-Waage
HX_ENTRY_SCK = 5
HX_PLATES_DT = 12           # Waage unter den Näpfen
HX_PLATES_SCK = 13

# RFID (SPI: sck, mosi, miso, rst, cs)
rdr = MFRC522(spi_id=1, sck=14, mosi=15, miso=16, cs=17, rst=18)

# HC-SR04 ultrasonic sensors for silo fill-level detection
ultra_silo1 = HCSR04(trigger_pin=21, echo_pin=22)  # HC-SR005
ultra_silo2 = HCSR04(trigger_pin=23, echo_pin=24)  # HC-SR004

# CD-ROM Laufwerkssteuerung
CD_POWER = Pin(1, Pin.OUT)
CD1_CTRL = Pin(3, Pin.OUT)
CD2_CTRL = Pin(2, Pin.OUT)

# --- INIT ---
entry_servo = PWM(Pin(SERVO_ENTRY_LOCK_PIN), freq=50)
plate1_servo = PWM(Pin(SERVO_PLATE1_LOCK_PIN), freq=50)
plate2_servo = PWM(Pin(SERVO_PLATE2_LOCK_PIN), freq=50)
schnecke1 = Pin(SCHNECKE1_PIN, Pin.OUT)
schnecke2 = Pin(SCHNECKE2_PIN, Pin.OUT)
hx_entry = HX711(d_out=Pin(HX_ENTRY_DT), pd_sck=Pin(HX_ENTRY_SCK))
hx_plate = HX711(d_out=Pin(HX_PLATES_DT), pd_sck=Pin(HX_PLATES_SCK))

# --- FUNCTIONS ---


def read_rfid():
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, raw_uid) = rdr.anticoll()
        if stat == rdr.OK:
            uid_str = "".join("%02X" % b for b in raw_uid)
            return uid_str
    return None


def check_connection():
    try:
        resp = urequests.get(f"{API_BASE}/backend/connection")
        print("Backend response:", resp.text)
        return True
    except Exception as e:
        print("Backend unreachable:", e)
        return False


def get_pet(rfid):
    try:
        resp = urequests.get(f"{API_BASE}/pet/get/{rfid}")
        return resp.json()
    except:
        return None


def confirm_feeding(rfid, scale_value):
    try:
        urequests.post(
            f"{API_BASE}/feeding/confirm?rfid={rfid}&newScaleWeight={scale_value}")
    except:
        print("Failed to confirm feeding")


def unlock_servo(servo):
    servo.duty(40)  # Open
    time.sleep(1)
    servo.duty(77)  # Close


def dispense_food(pin, duration=2):
    pin.on()
    time.sleep(duration)
    pin.off()


def read_scale(hx):
    try:
        val = hx.read()
        return val if val is not None else -1
    except:
        return -1


def cat_inside():
    try:
        weight = read_scale(hx_entry)
        return weight > 5000  # Schwelle fuer "Katze in Box" anpassen
    except:
        return False


def check_silo_fill(silo):
    try:
        if silo == 1:
            dist = ultra_silo1.distance_cm()
        elif silo == 2:
            dist = ultra_silo2.distance_cm()
        else:
            return -1
        return dist
    except:
        return -1


def close_cd(plate):
    if plate == 1:
        CD1_CTRL.on()
    elif plate == 2:
        CD2_CTRL.on()
    time.sleep(0.5)
    CD_POWER.off()
    time.sleep(1)
    CD1_CTRL.off()
    CD2_CTRL.off()


# --- MAIN LOOP ---
def main():
    if not check_connection():
        return

    while True:
        print("Waiting for cat...")
        rfid = read_rfid()
        if rfid:
            print("RFID detected:", rfid)
            if cat_inside():
                print("Box occupied, skipping")
                time.sleep(2)
                continue
            pet = get_pet(rfid)
            if pet:
                assigned_silo = pet.get("silo")
                # Check silo fill-level before proceeding
                fill_distance = check_silo_fill(assigned_silo)
                if fill_distance > 25:
                    print(
                        f"Silo {assigned_silo} möglicherweise leer! Abstand: {fill_distance}cm")
                    continue
                unlock_servo(entry_servo)
                time.sleep(1)  # Zeit fuer Katze zum Betreten
                if not cat_inside():
                    print("No cat entered, aborting")
                    continue
                if assigned_silo == 1:
                    unlock_servo(plate1_servo)
                    dispense_food(schnecke1)
                elif assigned_silo == 2:
                    unlock_servo(plate2_servo)
                    dispense_food(schnecke2)
                scale = read_scale(hx_plate)
                confirm_feeding(rfid, scale)

                # Warten bis Katze wieder raus ist
                print("Warte auf das Verlassen der Box...")
                while cat_inside():
                    time.sleep(1)
                close_cd(assigned_silo)
            else:
                print("Unknown pet, notifying backend")
                urequests.get(f"{API_BASE}/pet/unknown?rfid={rfid}")
        time.sleep(0.5)


if __name__ == '__main__':
    main()
