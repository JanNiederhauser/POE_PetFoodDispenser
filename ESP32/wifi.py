import network
import ujson
import time
import socket
import os

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
            return True
        time.sleep(1)
    print("Failed to connect.")
    return False

def start_config_portal():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid="ESP32-Setup")

    html = """<!DOCTYPE html>
<html><head><title>WiFi Setup</title></head>
<body>
<h2>Configure Wi-Fi</h2>
<form action="/" method="get">
SSID: <input name="s"><br>
Password: <input name="p" type="password"><br>
<input type="submit" value="Save">
</form>
</body></html>"""

    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)

    print("Config portal running at 192.168.4.1")

    while True:
        conn, addr = s.accept()
        req = conn.recv(1024).decode()
        if "/?s=" in req and "&p=" in req:
            try:
                parts = req.split("GET /?s=")[1].split(" ")[0]
                ssid, password = parts.split("&p=")
                ssid = ssid.replace("%20", " ")
                save_wifi(ssid, password)
                conn.send("HTTP/1.1 200 OK\r\n\r\nSaved! Rebooting...")
                conn.close()
                time.sleep(2)
                machine.reset()
            except:
                pass
        conn.send("HTTP/1.1 200 OK\r\n\r\n" + html)
        conn.close()
