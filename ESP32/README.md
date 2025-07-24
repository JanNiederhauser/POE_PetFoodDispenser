# 🐾 ESP32-C6 Pet Feeder Setup with MicroPython

This project documents how to set up an **ESP32-C6 DevKitC-1** board with **MicroPython**, including Wi-Fi onboarding via a web portal.

---

## ✅ Hardware Used

- **ESP32-C6 DevKitC-1** by Espressif
- USB-C cable (data-capable)

---

## 🧰 Software Requirements

### Install Python & Tools

```bash
pip install esptool mpremote
```
Download Driver (If ESP32 is not detected by Windows)
https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers?tab=downloads
---

## 🔥 Flashing MicroPython

### 1. Download the latest MicroPython build for ESP32-C6

➡️ https://micropython.org/download/ESP32_GENERIC_C6/

Pick the one under **ESP32-C6**, e.g.:
```
esp32-c6-20240609-v1.23.0-55-g7d4e3e108.bin
```

### 2. Erase flash (recommended)

```bash
esptool.py --chip esp32c6 --port COM3 erase_flash
```

Replace `COM3` with your actual serial port. Can be checked in device manager

### 3. Flash the firmware

```bash
esptool --chip esp32c6 --port COM3 --baud 115200 write_flash 0 'ESP32_GENERIC_C6-20250415-v1.25.0 (1).bin'
```

---

## 🚀 Connecting via REPL

```bash
mpremote connect auto
```

You should see:
```
MicroPython v1.xx on 202x-xx-xx; ESP32-C6 with ESP32-C6
>>>
```

---

## 🌐 Wi-Fi Setup Web Portal

### Files to upload:

- `main.py`
- `wifi.py`

### 1. Upload files

```bash
mpremote connect auto fs cp wifi.py :
mpremote connect auto fs cp main.py :
mpremote connect auto fs cp index.html :
mpremote connect auto fs cp nexani_logo_transparent.webp :
```

### 2. Reboot the ESP32

If `wifi.json` is not found, the device creates an Access Point named `ESP32-Setup`. Connect to it and visit `http://192.168.4.1` to enter your Wi-Fi credentials.

These credentials will be saved in `wifi.json`.

---

## 🧪 Device Control via REPL (MicroPython)

You can use the MicroPython REPL to inspect files and reboot the ESP32 manually.

### 📂 List and Delete Files

Use the following commands to view or delete files stored on the device:

```python
import os
```

List all files in the root directory
```python
print(os.listdir())
```

Delete a specific file (e.g., boot.py)
```python
os.remove("boot.py")
```

### 🔄 Reboot the Device
To trigger a soft reboot from the REPL:

python
```python
import machine
machine.reset()
```

## 📁 Project File Overview

| File        | Purpose                             |
|-------------|-------------------------------------|
| `main.py`   | Runs on boot, connects to Wi-Fi     |
| `wifi.py`   | Contains logic for AP and STA modes |
| `wifi.json` | Stores saved SSID/password          |
