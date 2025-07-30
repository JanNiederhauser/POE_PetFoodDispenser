import network
import socket
import os
import ujson
import machine
import neopixel
import _thread
import time

# --- LED Setup ---
LED_PIN = 8
np = neopixel.NeoPixel(machine.Pin(LED_PIN), 1)


def set_led(color, brightness=0.1):
    try:
        base = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "purple": (255, 0, 255),
            "off": (0, 0, 0)
        }
        raw = base.get(color, (255, 0, 255))
        scaled = tuple(int(x * brightness) for x in raw)
        np[0] = scaled
        np.write()
    except Exception as e:
        print(f"LED error: {str(e)}")

# --- Global variables ---
wlan_sta = None
config_portal_running = False

# --- DNS Server: answers all queries with 192.168.4.1 ---


def captive_dns():
    ip = '192.168.4.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 53))
    while True:
        try:
            data, addr = s.recvfrom(512)
            # Basic DNS response for any request, always with our IP
            response = (
                data[:2] + b'\x81\x80' + data[4:6]*2 + b'\x00\x00\x00\x00' +
                data[12:] +
                b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x1e\x00\x04' +
                bytes([int(x) for x in ip.split('.')])
            )
            s.sendto(response, addr)
        except Exception as e:
            print("DNS error:", e)

# --- Wi-Fi scan ---


def scan_and_save_wifi():
    print("🔍 Scanning WiFi networks...")
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        time.sleep(2)  # Give time for WiFi to activate
        nets = wlan.scan()
        ssids = sorted(set(net[0].decode('utf-8', 'ignore')
                       for net in nets if net[0] and len(net[0]) > 0), key=lambda x: x.lower())
        print(f"📡 Found {len(ssids)} networks")
        with open("wifiscan.json", "w") as f:
            ujson.dump(ssids, f)
        return True
    except Exception as e:
        print(f"❌ WiFi scan error: {e}")
        return False

# --- Save/load credentials ---
WIFI_FILE = "wifi.json"


def save_wifi(ssid, password):
    with open(WIFI_FILE, "w") as f:
        ujson.dump({"ssid": ssid, "password": password}, f)


def load_wifi():
    if WIFI_FILE in os.listdir():
        with open(WIFI_FILE) as f:
            return ujson.load(f)
    return None

# --- Wi-Fi connect ---


def connect_to_wifi(timeout=30):
    global wlan_sta
    creds = load_wifi()
    if not creds:
        print("No WiFi credentials found")
        return False
    
    try:
        # Reset network interfaces first
        print("Resetting network interfaces...")
        wlan_sta = network.WLAN(network.STA_IF)
        wlan_sta.active(False)
        time.sleep(1)
        wlan_sta.active(True)
        time.sleep(2)
        
        if wlan_sta.isconnected():
            ip = wlan_sta.ifconfig()[0]
            print(f"Already connected! IP: {ip}")
            set_led("green")
            return True
        
        print(f"Connecting to: {creds['ssid']}")
        set_led("yellow")
        
        # Disconnect any existing connection
        try:
            wlan_sta.disconnect()
            time.sleep(1)
        except:
            pass
        
        # Connect with explicit parameters
        wlan_sta.connect(creds["ssid"], creds["password"])
        
        # Wait for connection with detailed status
        for attempt in range(timeout):
            status = wlan_sta.status()
            
            if wlan_sta.isconnected():
                ip = wlan_sta.ifconfig()[0]
                print(f"WiFi connected! IP: {ip}")
                set_led("green")
                return True
            
            # Print status every 5 seconds
            if attempt % 5 == 0:
                status_msg = {
                    0: "IDLE",
                    1: "CONNECTING", 
                    2: "WRONG_PASSWORD",
                    3: "NO_AP_FOUND",
                    4: "CONNECT_FAIL",
                    5: "GOT_IP"
                }.get(status, f"UNKNOWN({status})")
                print(f"Status: {status_msg} (attempt {attempt + 1}/{timeout})")
            
            # Handle specific error conditions
            if status == 2:  # WRONG_PASSWORD
                print("Wrong password - check credentials")
                set_led("red")
                wlan_sta.active(False)
                return False
            elif status == 3:  # NO_AP_FOUND
                print("Access point not found - check SSID")
                set_led("red")
                wlan_sta.active(False)
                return False
            elif status == 4:  # CONNECT_FAIL
                print("Connection failed - retrying...")
                wlan_sta.disconnect()
                time.sleep(2)
                wlan_sta.connect(creds["ssid"], creds["password"])
            
            time.sleep(1)
        
        print("Connection timeout")
        wlan_sta.active(False)
        set_led("red")
        return False
        
    except Exception as e:
        # Convert any problematic characters to safe string
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"WiFi connection error: {error_msg}")
        set_led("purple")
        try:
            if wlan_sta:
                wlan_sta.active(False)
        except:
            pass
        return False

def reset_network():
    """Reset all network interfaces"""
    print("Performing network reset...")
    try:
        # Reset STA interface
        wlan_sta = network.WLAN(network.STA_IF)
        wlan_sta.active(False)
        
        # Reset AP interface  
        wlan_ap = network.WLAN(network.AP_IF)
        wlan_ap.active(False)
        
        time.sleep(2)
        print("Network interfaces reset")
        return True
    except Exception as e:
        print(f"Network reset error: {str(e)}")
        return False

def is_connected():
    """Check if WiFi is connected"""
    global wlan_sta
    if wlan_sta is None:
        return False
    return wlan_sta.isconnected()

def get_ip():
    """Get current IP address"""
    global wlan_sta
    if wlan_sta and wlan_sta.isconnected():
        return wlan_sta.ifconfig()[0]
    return None

def reconnect_wifi():
    """Attempt to reconnect WiFi"""
    print("🔄 Attempting WiFi reconnection...")
    if connect_to_wifi(timeout=15):
        return True
    print("❌ WiFi reconnection failed")
    return False

def start_config_portal():
    global config_portal_running
    if config_portal_running:
        print("⚠️ Config portal already running")
        return
        
    config_portal_running = True
    print("🔧 Starting WiFi configuration portal...")
    
    try:
        # Start AP
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid="Nexani-Setup", password="")  # Open network for easier setup
        print("📡 Access Point 'Nexani-Setup' started")
        set_led("blue")
        
        # Scan networks
        if not scan_and_save_wifi():
            print("⚠️ WiFi scan failed, continuing with empty list")
        
        # Start DNS in thread
        print("🌐 Starting captive DNS server...")
        try:
            _thread.start_new_thread(captive_dns, ())
        except Exception as e:
            print(f"❌ Failed to start DNS thread: {e}")
        
        # Start HTTP server
        serve_config_portal()
        
    except Exception as e:
        print(f"❌ Config portal error: {e}")
        set_led("red")
    finally:
        config_portal_running = False

def serve_config_portal():
    """HTTP server for config portal"""
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(2)
        print("🌐 Config portal running at http://192.168.4.1")
        
        while config_portal_running:
            try:
                s.settimeout(5)  # 5 second timeout
                conn, addr = s.accept()
                print(f"📥 Request from {addr}")
                
                try:
                    req = conn.recv(1024)
                    if not req:
                        conn.close()
                        continue
                    req = req.decode("utf-8")
                    
                    # Handle different requests
                    handle_request(conn, req)
                    
                except Exception as e:
                    print(f"❌ Request handling error: {e}")
                finally:
                    try:
                        conn.close()
                    except:
                        pass
                        
            except OSError as e:
                if e.errno != 116:  # Not timeout error
                    print(f"❌ Socket error: {e}")
                    break
            except Exception as e:
                print(f"❌ Config portal error: {e}")
                break
                
    except Exception as e:
        print(f"❌ Failed to start HTTP server: {e}")
    finally:
        try:
            s.close()
        except:
            pass

def handle_request(conn, req):
    """Handle individual HTTP requests"""
    try:
        # Save Wi-Fi credentials
        if "/?s=" in req and "&p=" in req:
            try:
                parts = req.split("GET /?s=")[1].split(" ")[0]
                ssid, password = parts.split("&p=")
                ssid = ssid.replace("%20", " ").replace("+", " ")
                password = password.replace("%20", " ").replace("+", " ")
                print(f"💾 Saving WiFi credentials for SSID: {ssid}")
                save_wifi(ssid, password)
                conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                conn.send(b"<html><body><h1>Saved!</h1><p>Rebooting device...</p></body></html>")
                time.sleep(1)
                machine.reset()
            except Exception as e:
                print(f"❌ Parse error: {e}")
                conn.send(b"HTTP/1.1 400 Bad Request\r\n\r\nError parsing credentials")
                
        # Serve Wi-Fi scan
        elif "GET /wifiscan.json" in req:
            try:
                if "wifiscan.json" in os.listdir():
                    with open("wifiscan.json", "r") as f:
                        data = f.read()
                    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
                    conn.send(data.encode())
                else:
                    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n[]")
            except Exception as e:
                print(f"❌ WiFi scan serve error: {e}")
                conn.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\nScan error")
                
        # Serve logo
        elif "GET /nexani_logo_transparent.webp" in req:
            try:
                with open("nexani_logo_transparent.webp", "rb") as f:
                    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: image/webp\r\n\r\n")
                    while True:
                        data = f.read(1024)
                        if not data:
                            break
                        conn.send(data)
            except:
                conn.send(b"HTTP/1.1 404 Not Found\r\n\r\nLogo not found")
                
        # Serve index.html
        elif "GET / " in req or "GET /index.html" in req:
            try:
                with open("index.html") as f:
                    html = f.read()
                conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                conn.send(html.encode())
            except:
                conn.send(b"HTTP/1.1 404 Not Found\r\n\r\nConfig page not found")
                
        # Redirect all other paths
        else:
            conn.send(b"HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
            
    except Exception as e:
        print(f"❌ Request handler error: {e}")
        try:
            conn.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\nServer error")
        except:
            pass

def init_wifi():
    """Initialize WiFi - call this from main.py"""
    print("Initializing WiFi manager...")
    
    # Reset network first
    reset_network()
    
    # Try to connect
    if connect_to_wifi():
        print("WiFi connection established")
        ip = get_ip()
        if ip:
            print(f"IP Address: {ip}")
        return True
    else:
        print("WiFi not configured or connection failed")
        print("Manual setup required")
        print("Connect to 'Nexani-Setup' AP and visit http://192.168.4.1")
        
        # Only start config portal in interactive mode
        try:
            # Check if we're in interactive mode
            import sys
            if hasattr(sys, 'ps1'):
                start_config_portal()
            else:
                print("Config portal disabled in non-interactive mode")
        except:
            print("Config portal disabled")
        
        return False

# --- Main entrypoint (only run if called directly) ---
if __name__ == "__main__":
    init_wifi()
