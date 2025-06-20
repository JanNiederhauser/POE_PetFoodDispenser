import network
import ujson
import time
import socket
import os
import machine
import neopixel

# Setup RGB LED on GPIO 8
LED_PIN = 8
np = neopixel.NeoPixel(machine.Pin(LED_PIN), 1)


def set_led(color, brightness=0.08):  # 0.0 (off) to 1.0 (full)
    base_colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "off": (0, 0, 0)
    }
    raw = base_colors.get(color, (255, 0, 255))  # fallback = purple = error
    # scale by brightness (clamped 0..255)
    scaled = tuple(int(x * brightness) for x in raw)
    np[0] = scaled
    np.write()



WIFI_FILE = "wifi.json"


def save_wifi(ssid, password):
    with open(WIFI_FILE, "w") as f:
        ujson.dump({"ssid": ssid, "password": password}, f)


def load_wifi():
    if WIFI_FILE in os.listdir():
        with open(WIFI_FILE) as f:
            return ujson.load(f)
    return None


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


def scan_and_save_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    nets = wlan.scan()
    ssids = sorted(set(net[0].decode()
                   for net in nets if net[0]), key=lambda x: x.lower())
    with open("wifiscan.json", "w") as f:
        ujson.dump(ssids, f)


def start_config_portal():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="ESP32-Setup")

    set_led("blue")

    # Scan and save wifi SSIDs
    scan_and_save_wifi()

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print("Config portal running at 192.168.4.1")

    while True:
        try:
            conn, addr = s.accept()
            req = conn.recv(1024)

            if not req:
                conn.close()
                continue

            req = req.decode("utf-8")

            # Handle Wi-Fi credentials via GET
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


            elif "GET /nexani_logo_transparent.png" in req:
                try:
                    with open("nexani_logo_transparent.png", "rb") as f:
                        conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n")
                        while True:
                            data = f.read(1024)
                            if not data:
                                break
                            conn.send(data)
                except Exception as e:
                    print("Logo error:", e)
                    conn.send(b"HTTP/1.1 404 Not Found\r\n\r\nNot Found")


            elif "GET /" in req or "GET /index.html" in req:
                with open("index.html") as f:
                    html = f.read()
                conn.send(
                    "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)

            else:
                conn.send("HTTP/1.1 404 Not Found\r\n\r\nNot Found")

            conn.close()

        except Exception as e:
            print("Config portal error:", e)
            set_led("red")
