# boot.py
import wifi
import time
import machine

print("🚀 Pet Food Dispenser Starting...")

# Initialize WiFi connection
if wifi.init_wifi():
    print("✅ WiFi ready, starting dispenser...")
    time.sleep(1)
    
    # Import and run the pet food dispenser
    try:
        import petfooddispenser
        print("✅ Pet food dispenser module loaded successfully")
    except Exception as e:
        print(f"❌ Failed to start pet food dispenser: {e}")
        print("🔄 System will restart in 10 seconds...")
        time.sleep(10)
        machine.reset()
else:
    print("⚠️ WiFi not configured - please set up WiFi first")
    print("💡 Connect to 'Nexani-Setup' AP and visit http://192.168.4.1")
    # Stay in config mode indefinitely
    while True:
        time.sleep(10)
        print("📡 Waiting for WiFi configuration...")
