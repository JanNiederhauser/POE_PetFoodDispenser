# boot.py
import wifi
import time
import machine

# Retry WLAN init and fall back to config portal
if not wifi.connect_to_wifi():
    print("WiFi not configured, entering portal mode...")
    wifi.start_config_portal()
    while not wifi.wlan.isconnected():
        time.sleep(1)

# Wait briefly before launching main system
print("WiFi ready, starting dispenser...")
time.sleep(1)
#machine.main("petfooddispenser.py")  # Start modified main logic
