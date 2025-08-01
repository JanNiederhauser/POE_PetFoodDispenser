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
SERVO_LOCK = 120
SERVO_UNLOCKED = 30
SCHNECKE1_PIN = 1         # GPIO10 - Motor to dispense food (silo 1)
SCHNECKE2_PIN = 7          # GPIO11 - Motor to dispense food (silo 2)

# HX711 pins
HX_ENTRY_DT = 15             # Eingangs-Waage
HX_ENTRY_SCK = 4
HX_PLATES_DT = 12          # Waage unter den Näpfen
HX_PLATES_SCK = 4
HX_channel = 3
threshhold = 50

Pin(HX_ENTRY_SCK, Pin.IN)   # high-Z
Pin(HX_ENTRY_DT, Pin.IN)     # high-Z
Pin(HX_PLATES_SCK, Pin.IN)  # high-Z
#Pin(HX_PLATES_DT, Pin.IN)    # high-Z

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
ultra_silo2 = HCSR04(trigger_pin=10, echo_pin=2)  # HC-SR004 rechts

# CD-ROM Laufwerkssteuerung
CD1_CTRL = Pin(11, Pin.OUT, value=1)
CD2_CTRL = Pin(8, Pin.OUT, value=1)
time.sleep(0.2)
CD_POWER = Pin(3, Pin.OUT, value=0)

# --- INIT ---
print("🏗️ Initializing hardware components...")
entry_servo = PWM(Pin(SERVO_ENTRY_LOCK_PIN), freq=50)
entry_servo.duty(SERVO_LOCK)  # Set initial position to closed
schnecke1 = Pin(SCHNECKE1_PIN, Pin.OUT, value=1)
schnecke2 = Pin(SCHNECKE2_PIN, Pin.OUT, value=1)
hx_entry = HX711(HX_ENTRY_SCK, HX_ENTRY_DT)
#hx_plate = HX711(HX_PLATES_SCK, HX_PLATES_DT)
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
        #resp = urequests.get(f"{API_BASE}/feeding/check/{rfid}")
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
    servo.duty(SERVO_UNLOCKED)  # Open
    print("✅ Servo unlocked")


def lock_servo(servo):
    print("🔓 Locking servo...")
    servo.duty(SERVO_LOCK)  # closed
    print("❌ Servo locked")


def dispense_food(schnecke, target_weight_grams, foodDuration):
    print(f"🥘 Dispensing food until {target_weight_grams}g is reached...")
    #TODO fix this
    hx_entry.powerDown()
    time.sleep(0.1)  # Allow HX711 to stabilize
    #hx_plate.powerUp()
    time.sleep(0.1)  # Allow HX711 to stabilize
    # Get initial weight
    #hx_plate.tare()  # Reset tare to zero
    #initial_weight = 0# abs(hx_plate.read()) * 3.3
    #if initial_weight == -1:
    #    print("❌ Cannot read initial weight, aborting dispensing")
    #    return
    #
    #target_total_weight = initial_weight + target_weight_grams
    #print(f"📊 Initial weight: {initial_weight}g, Target total: {target_total_weight}g")
    
    schnecke.off()  # Start dispensing
    time.sleep(foodDuration)
    #try:
    #    while True:
    #        consecutive_reaches = 0  # Counter for consecutive target weight reaches
    #        
    #        while True:
    #            current_weight = hx_plate.read()
    #            if current_weight == -1:
    #                print("❌ Scale reading failed during dispensing")
    #                break
    #            
    #            dispensed_amount = current_weight - initial_weight
    #            print(f"📊 Current: {current_weight}g, Dispensed: {dispensed_amount}g")
    #            
    #            if current_weight >= target_total_weight:
    #                consecutive_reaches += 1
    #                if consecutive_reaches >= 2:  # Require two consecutive confirmations
    #                    print(f"✅ Target weight reached! Dispensed {dispensed_amount}g")
    #                    break
    #            else:
    #                consecutive_reaches = 0  # Reset counter if target not reached
    #            
    #            time.sleep(0.5)  # Check weight every 0.5 seconds
    #        
    #finally:
    #    schnecke.on()  # Always turn off the motor
    #    print("✅ Food dispensing complete")
    schnecke.on()  # Always turn off the motor
    hx_entry.powerUp()
    time.sleep(0.1)  # Allow HX711 to stabilize
    print("✅ Food dispensing complete")


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


def cat_inside(catDetectionWeightEvent):
    try:
        # Try to get a reading from the HX711
        try:
            raw_weight = hx_entry.read()
        except Exception as read_error:
            print(f"❌ HX711 read error: {read_error}")
            return False
        
        # Handle None or invalid readings
        if raw_weight is None:
            print("❌ No weight reading available")
            return False
        
        # Simple type checking and conversion
        try:
            if isinstance(raw_weight, str):
                # Try to convert string to number
                weight_num = float(raw_weight)
            elif isinstance(raw_weight, (int, float)):
                weight_num = float(raw_weight)
            else:
                print(f"❌ Unexpected weight type: {type(raw_weight)}")
                return False
            
            # Apply calibration factor
            weight = abs(weight_num) * 3.3
            
        except (ValueError, TypeError) as conv_error:
            print(f"❌ Weight conversion error: {conv_error}")
            return False
            
        # Check if cat is inside
        inside = weight > catDetectionWeightEvent
        print(f"Cat detection: {'INSIDE' if inside else 'OUTSIDE'} (weight: {weight:.1f}g, threshold: {catDetectionWeightEvent}g)")
        
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
    if plate == 2:
        CD1_CTRL(0)
        time.sleep(0.2)
        CD_POWER(0)  # CD-ROM Laufwerk einschalten
        time.sleep(1.5)
        CD_POWER(1)  # CD-ROM Laufwerk ausschalten
        CD1_CTRL(1)
    elif plate == 1:
        CD2_CTRL(0)
        time.sleep(0.2)
        CD_POWER(0)  # CD-ROM Laufwerk einschalten
        time.sleep(1.5)
        CD_POWER(1)  # CD-ROM Laufwerk ausschalten
        CD2_CTRL(1)
    elif plate == 0:
        CD_POWER(0)
    print(f"✅ CD tray {plate} closed")


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
            # pet = get_pet(rfid)  # Authenticate pet using backend API
            data = urequests.post(f"{API_BASE}/feeding/check/{rfid}")
            # for test changed to = 404
            if data.status_code == 404:
                # Calibrate HX711 scales
                print("Calibrating scales...")
                hx_entry.powerUp()
                time.sleep(0.1)  # Allow HX711 to stabilize
                entryScaleInitialWeight = 0 #abs(hx_entry.read()) * 3.3 # Adjusted for calibration factor
                catDetectionWeightEvent = entryScaleInitialWeight + threshhold
                hx_entry.tare()  # Reset tare to zero
                print(f"Entry scale initial weight: {entryScaleInitialWeight}")
                print(f"Cat detection threshold: {catDetectionWeightEvent}")

                data = {"name": "DummyPet", "silo": 2, "foodamount": 100, "foodDuration": 5}
                print(f"Pet authenticated: {data['name']}")
                assigned_silo = data.get("silo")
                print(f"Assigned silo: {assigned_silo}")
                
                # Check silo fill-level before proceeding
                fill_distance = check_silo_fill(assigned_silo)
                max_distance = 30  # Distance when silo is empty
                min_distance = 5   # Distance when silo is full

                if fill_distance > max_distance:
                    print(f"Silo {assigned_silo} possibly empty! Distance: {fill_distance}cm")
                    continue
                elif fill_distance <= max_distance and fill_distance > min_distance:
                    fill_percentage = int((max_distance - fill_distance) / (max_distance - min_distance) * 100)
                    print(f"Silo {assigned_silo} fill level: {fill_percentage}%")
                elif fill_distance <= min_distance:
                    print(f"Silo {assigned_silo} is full! Distance: {fill_distance}cm")
                
                print("Unlocking entry...")
                unlock_servo(entry_servo)
                hx_entry.powerUp()  # Power up the HX711 for entry scale
                hx_entry.read()
                time.sleep(1)  # Wait for servo to unlock
                start_time = time.time()
                consecutive_detections = 0

                while time.time() - start_time < 30:
                    if cat_inside(catDetectionWeightEvent):
                        consecutive_detections += 1
                        if consecutive_detections >= 3:  # Require 3 consecutive detections
                            print("✅ Cat entered, proceeding with feeding cycle")
                            break
                    else:
                        consecutive_detections = 0  # Reset if detection fails
                    time.sleep(1)  # Check every second
                else:
                    print("❌ No cat entered within 30 seconds, aborting feeding cycle")
                    continue
                
                print("Cat detected inside, proceeding with feeding...")
                
                # Close the entry servo
                print("Closing entry servo...")
                lock_servo(entry_servo)

                if assigned_silo == 1:
                    print("Opening plate 1 and dispensing from silo 1")
                    close_cd(1)
                    dispense_food(schnecke1, data['foodamount'], data['foodDuration'])
                elif assigned_silo == 2:
                    print("Opening plate 2 and dispensing from silo 2")
                    close_cd(2)
                    dispense_food(schnecke2,data['foodamount'], data['foodDuration'])
                
                #scale = read_scale(hx_plate)
                #confirm_feeding(rfid, scale)

                # Warten bis Katze wieder raus ist
                print("Waiting for cat to exit...")
                consecutive_no_detections = 0

                while True:
                    if not cat_inside(catDetectionWeightEvent):
                        consecutive_no_detections += 1
                        if consecutive_no_detections >= 3:  # Require 3 consecutive non-detections
                            print("✅ Cat has exited")
                            break
                    else:
                        consecutive_no_detections = 0  # Reset if cat still detected
                        print("Cat still inside...")
                    time.sleep(1)  # Check every second
                
                print("✅ Feeding cycle complete")
                time.sleep(5)
                close_cd(0)  # Close CD tray after feeding
                
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
# Actually run the main function
print("Starting Pet Food Dispenser...")
main()
