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
    base = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "off": (0, 0, 0)
    }
    raw = base.get(color, (255, 0, 255))
    scaled = tuple(int(x * brightness) for x in raw)
    np[0] = scaled
    np.write()

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
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    nets = wlan.scan()
    ssids = sorted(set(net[0].decode()
                   for net in nets if net[0]), key=lambda x: x.lower())
    with open("wifiscan.json", "w") as f:
        ujson.dump(ssids, f)


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


def connect_to_wifi():
    creds = load_wifi()
    if not creds:
        return False
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(creds["ssid"], creds["password"])
    print(f"Connecting to {creds['ssid']}...")
    for _ in range(20):
        if wlan.isconnected():
            print("Connected:", wlan.ifconfig())
            set_led("green")
            return True
        time.sleep(1)
    print("Failed to connect.")
    set_led("red")
    return False

# --- Web Server (Captive Portal) ---


def start_config_portal():
    # Start AP
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="ESP32-Setup")
    set_led("blue")
    # Scan networks
    scan_and_save_wifi()
    # Start DNS in thread
    _thread.start_new_thread(captive_dns, ())
    # Start HTTP server
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(2)
    print("Config portal running at http://192.168.4.1")
    while True:
        try:
            conn, addr = s.accept()
            req = conn.recv(1024)
            if not req:
                conn.close()
                continue
            req = req.decode("utf-8")
            # --- Save Wi-Fi credentials ---
            if "/?s=" in req and "&p=" in req:
                try:
                    parts = req.split("GET /?s=")[1].split(" ")[0]
                    ssid, password = parts.split("&p=")
                    ssid = ssid.replace("%20", " ")
                    save_wifi(ssid, password)
                    conn.send(
                        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nSaved! Rebooting...")
                    conn.close()
                    time.sleep(2)
                    machine.reset()
                except Exception as e:
                    print("Parse error:", e)
                    set_led("red")
            # --- Serve Wi-Fi scan ---
            elif "GET /wifiscan.json" in req:
                if "wifiscan.json" in os.listdir():
                    with open("wifiscan.json", "r") as f:
                        data = f.read()
                    conn.send(
                        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
                    conn.send(data)
                else:
                    conn.send(
                        b"HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\nNo scan")
            # --- Serve logo (in chunks!) ---
            elif "GET /nexani_logo_transparent.webp" in req:
                try:
                    with open("nexani_logo_transparent.webp", "rb") as f:
                        conn.send(
                            b"HTTP/1.1 200 OK\r\nContent-Type: image/webp\r\n\r\n")
                        while True:
                            data = f.read(1024)
                            if not data:
                                break
                            conn.send(data)
                except Exception as e:
                    print("Logo error:", e)
                    conn.send(b"HTTP/1.1 404 Not Found\r\n\r\nNot Found")
            # --- Serve index.html ---
            elif "GET / " in req or "GET /index.html" in req:
                with open("index.html") as f:
                    html = f.read()
                conn.send(
                    "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)
            # --- HTTP redirect for all other paths (Captive Portal magic) ---
            else:
                conn.send("HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")
            conn.close()
        except Exception as e:
            print("Config portal error:", e)
            set_led("red")


# --- Main entrypoint ---
if not connect_to_wifi():
    start_config_portal()
