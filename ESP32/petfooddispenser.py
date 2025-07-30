# dispenser_main.py - Pet Food Dispenser Controller for ESP32-C6 (MicroPython)

import machine
import time
import urequests
from machine import Pin, PWM
from mfrc522 import MFRC522
from hcsr04 import HCSR04
from hx711 import HX711
from machine import Pin, SoftSPI

# --- CONFIGURATION ---
API_BASE = "http://192.168.2.169:8000"  # Replace with your actual Windows IP
print("🔧 Initializing Pet Food Dispenser...")
print(f"📡 Backend API: {API_BASE}")

SERVO_ENTRY_LOCK_PIN = 9    # GPIO6 - Entry servo
SCHNECKE1_PIN = 1         # GPIO10 - Motor to dispense food (silo 1)
SCHNECKE2_PIN = 7          # GPIO11 - Motor to dispense food (silo 2)

# HX711 pins
HX_ENTRY_DT = 15             # Eingangs-Waage
HX_ENTRY_SCK = 4
HX_PLATES_DT = 6          # Waage unter den Näpfen
HX_PLATES_SCK = 4
HX_channel = 3

# RFID (SPI: sck, mosi, miso, rst, cs)
sck = Pin(18, Pin.OUT)
copi = Pin(23, Pin.OUT)  # Controller out, peripheral in
cipo = Pin(19, Pin.OUT)  # Controller in, peripheral out
spi = SoftSPI(baudrate=100000, polarity=0, phase=0,
              sck=sck, mosi=copi, miso=cipo)
sda = Pin(5, Pin.OUT)
reader = MFRC522(spi, sda)

# HC-SR04 ultrasonic sensors for silo fill-level detection
ultra_silo1 = HCSR04(trigger_pin=20, echo_pin=22)  # HC-SR005 links
#ultra_silo2 = HCSR04(trigger_pin=12, echo_pin=13)  # HC-SR004 rechts  - funzt nicht

# CD-ROM Laufwerkssteuerung
CD1_1_CTRL = Pin(11, Pin.OUT, value=1)
CD1_2_CTRL = Pin(2, Pin.OUT, value=1)
CD2_1_CTRL = Pin(10, Pin.OUT, value=1)
CD2_2_CTRL = Pin(8, Pin.OUT, value=1)
time.sleep(0.2)
CD_POWER = Pin(3, Pin.OUT, value=1)

# --- INIT ---
print("🏗️ Initializing hardware components...")
#entry_servo = PWM(Pin(SERVO_ENTRY_LOCK_PIN), freq=50)
schnecke1 = Pin(SCHNECKE1_PIN, Pin.OUT, value=1)
schnecke2 = Pin(SCHNECKE2_PIN, Pin.OUT, value=1)
hx_entry = HX711(HX_ENTRY_DT, HX_ENTRY_SCK, HX_channel)
hx_plate = HX711(HX_PLATES_DT, HX_PLATES_SCK, HX_channel)
print("✅ Hardware initialization complete")

# --- FUNCTIONS ---
def read_weight(sensor):
    """Reads and prints the weight from the HX711 sensor."""
    print("⚖️ Reading weight sensor...")
    sensor.power_on()

    while sensor.is_ready():
        pass

    raw_measurement = sensor.read(False)

    while sensor.is_ready():
        pass

    raw_measurement = sensor.read(True)
    print(f"📊 Raw measurement: {raw_measurement}")

    weight = raw_measurement / 420
    print(f'⚖️ Total Weight: {weight}g')
    return weight


def read_rfid():
    """Reads the RFID UID using the MFRC522 module."""
    print("🔍 Scanning for RFID card...")
    (stat, tag_type) = reader.request(reader.CARD_REQIDL)  # Request RFID tag
    if stat == reader.OK:
        (stat, raw_uid) = reader.anticoll()  # Get UID
        if stat == reader.OK:
            # Convert UID to string
            uid_str = "".join("%02X" % b for b in raw_uid)
            print(f"🏷️ RFID UID detected: {uid_str}")
            return uid_str
    return None


def check_connection(retries=3, delay=2):
    print("🌐 Checking backend connection...")
    for attempt in range(retries):
        try:
            url = f"{API_BASE}/backend/health"
            print(f"🔗 Attempting API call to: {url}")
            resp = urequests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                resp.close()
                print(f"✅ Backend response: {data.get('status', 'Unknown')}")
                return True
            else:
                print(f"❌ Backend error: {resp.status_code} - {resp.text}")
                resp.close()
        except OSError as e:
            if e.errno == 104:  # ECONNRESET
                print(f"❌ Connection reset - backend may be down (attempt {attempt + 1}/{retries})")
            elif e.errno == 113:  # EHOSTUNREACH  
                print(f"❌ Host unreachable - check IP address and firewall (attempt {attempt + 1}/{retries})")
            elif e.errno == 110:  # ETIMEDOUT
                print(f"❌ Connection timeout - check network (attempt {attempt + 1}/{retries})")
            else:
                print(f"❌ Network error {e.errno}: {e} (attempt {attempt + 1}/{retries})")
        except Exception as e:
            print(f"❌ Backend unreachable (attempt {attempt + 1}/{retries}): {e}")
        
        if attempt < retries - 1:
            print(f"⏳ Waiting {delay} seconds before retry...")
            time.sleep(delay)
    
    print("❌ All connection attempts failed")
    return False


def get_pet(rfid):
    print(f"👤 Looking up pet with RFID: {rfid}")
    try:
        resp = urequests.get(f"{API_BASE}/pet/get/{rfid}")
        pet_data = resp.json()
        print(f"✅ Pet found: {pet_data}")
        return pet_data
    except Exception as e:
        print(f"❌ Pet lookup failed: {e}")
        return None


def confirm_feeding(rfid, scale_value):
    print(f"📝 Confirming feeding for RFID {rfid}, scale weight: {scale_value}g")
    try:
        urequests.post(f"{API_BASE}/feeding/confirm?rfid={rfid}&newScaleWeight={scale_value}")
        print("✅ Feeding confirmed with backend")
    except Exception as e:
        print(f"❌ Failed to confirm feeding: {e}")


def unlock_servo(servo):
    print("🔓 Unlocking servo...")
    # servo.duty(40)  # Open
    # time.sleep(1)
    # servo.duty(77)  # Close
    print("✅ Servo unlocked")


def dispense_food(pin, duration=2):
    print(f"🥘 Dispensing food for {duration} seconds...")
    pin.on()
    time.sleep(duration)
    pin.off()
    print("✅ Food dispensed")


def read_scale(hx):
    print("⚖️ Reading scale...")
    try:
        val = hx.read()
        result = val if val is not None else -1
        print(f"📊 Scale reading: {result}")
        return result
    except Exception as e:
        print(f"❌ Scale reading failed: {e}")
        return -1


def cat_inside():
    try:
        weight = read_scale(hx_entry)
        inside = weight > catDetectionWeightEvent
        print(f"Cat detection: {'INSIDE' if inside else 'OUTSIDE'} (weight: {weight}g, threshold: {catDetectionWeightEvent}g)")
        return inside
    except Exception as e:
        print(f"❌ Cat detection failed: {e}")
        return False


def check_silo_fill(silo):
    print(f"📏 Checking silo {silo} fill level...")
    try:
        if silo == 1:
            dist = ultra_silo1.distance_cm()
        elif silo == 2:
            # dist = ultra_silo2.distance_cm()
            print("⚠️ Silo 2 sensor not functional")
            return 10  # Assume good fill level
        else:
            print(f"❌ Invalid silo number: {silo}")
            return -1
        print(f"📏 Silo {silo} distance: {dist}cm")
        return dist
    except Exception as e:
        print(f"❌ Silo fill check failed: {e}")
        return -1


def close_cd(plate):
    print(f"📀 Closing CD tray for plate {plate}...")
    if plate == 1:
        CD1_1_CTRL(0)
        CD1_2_CTRL(0)
        time.sleep(0.2)
        CD_POWER(0)  # CD-ROM Laufwerk einschalten
        time.sleep(1.5)
        CD_POWER(1)  # CD-ROM Laufwerk ausschalten
        CD1_1_CTRL(1)
        CD1_2_CTRL(1)
    elif plate == 2:
        CD2_1_CTRL(0)
        CD2_2_CTRL(0)
        time.sleep(0.2)
        CD_POWER(0)  # CD-ROM Laufwerk einschalten
        time.sleep(1.5)
        CD_POWER(1)  # CD-ROM Laufwerk ausschalten
        CD2_1_CTRL(1)
        CD2_2_CTRL(1)
    print(f"✅ CD tray {plate} closed")


# Calibrate HX711 scales
print("Calibrating scales...")
entryScaleInitialWeight = hx_entry.read()
catDetectionWeightEvent = entryScaleInitialWeight + 150
print(f"Entry scale initial weight: {entryScaleInitialWeight}")
print(f"Cat detection threshold: {catDetectionWeightEvent}")


# --- MAIN LOOP ---
def main():
    print("Starting main feeding loop...")
    
    if not check_connection():
        print("❌ Cannot start - backend not available")
        return

    print("Main loop started - waiting for RFID scans...")
    
    while True:
        print("\n" + "="*50)
        print("Waiting for RFID...")
        rfid = read_rfid()  # Read RFID UID
        
        if rfid:
            print(f"RFID detected: {rfid}")
            pet = get_pet(rfid)  # Authenticate pet using backend API
            
            if pet:
                print(f"Pet authenticated: {pet['name']}")
                assigned_silo = pet.get("silo")
                print(f"Assigned silo: {assigned_silo}")
                
                # Check silo fill-level before proceeding
                fill_distance = check_silo_fill(assigned_silo)
                if fill_distance > 25:
                    print(f"Silo {assigned_silo} possibly empty! Distance: {fill_distance}cm")
                    continue
                
                print("Unlocking entry...")
                # unlock_servo(entry_servo)
                time.sleep(1)  # Zeit fuer Katze zum Betreten
                
                if not cat_inside():
                    print("❌ No cat entered, aborting feeding cycle")
                    continue
                
                print("Cat detected inside, proceeding with feeding...")
                
                if assigned_silo == 1:
                    print("Opening plate 1 and dispensing from silo 1")
                    # unlock_servo(plate1_servo)
                    dispense_food(schnecke1)
                elif assigned_silo == 2:
                    print("Opening plate 2 and dispensing from silo 2")
                    # unlock_servo(plate2_servo)
                    dispense_food(schnecke2)
                
                scale = read_scale(hx_plate)
                confirm_feeding(rfid, scale)

                # Warten bis Katze wieder raus ist
                print("Waiting for cat to exit...")
                while cat_inside():
                    time.sleep(1)
                    print("Cat still inside...")
                
                print("Cat has exited, closing plates...")
                close_cd(assigned_silo)
                print("✅ Feeding cycle complete")
                
            else:
                print(f"Unknown pet with RFID {rfid}, notifying backend")
                try:
                    urequests.get(f"{API_BASE}/dashboard/unknown-rfids?rfid={rfid}")
                    print("✅ Unknown RFID reported to backend")
                except Exception as e:
                    print(f"❌ Failed to report unknown RFID: {e}")
        
        time.sleep(0.5)

if __name__ == '__main__':
    main()

# Actually run the main function
print("Starting Pet Food Dispenser...")
main()
