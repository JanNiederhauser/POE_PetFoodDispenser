from machine import Pin, SoftSPI

from mfrc522 import MFRC522

sck = Pin(18, Pin.OUT)
copi = Pin(23, Pin.OUT) # Controller out, peripheral in
cipo = Pin(19, Pin.OUT) # Controller in, peripheral out
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=sck, mosi=copi, miso=cipo)
sda = Pin(5, Pin.OUT)
reader = MFRC522(spi, sda)

print('🔍 RFID Scanner Test Started')
print('📋 Place Card In Front Of Device To Read Unique Address')
print('=' * 50)

while True:
    try:
        (status, tag_type) = reader.request(reader.CARD_REQIDL)
        if status == reader.OK:
            print('🏷️ RFID signal detected...')
            (status, raw_uid) = reader.anticoll()
            if status == reader.OK:
                print('✅ New Card Detected')
                print(f'📊 Tag Type: 0x{tag_type:02x}')
                uid_hex = '0x%02x%02x%02x%02x' % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3])
                uid_string = ''.join('%02X' % b for b in raw_uid)
                print(f'🆔 UID (hex): {uid_hex}')
                print(f'🆔 UID (string): {uid_string}')
                print('-' * 30)
                
                if reader.select_tag(raw_uid) == reader.OK:
                    key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                    if reader.auth(reader.AUTH, 8, key, raw_uid) == reader.OK:
                        data = reader.read(8)
                        print(f"📖 Address Data: {data}")
                        reader.stop_crypto1()
                    else:
                        print("❌ AUTH ERROR")
                else:
                    print("❌ FAILED TO SELECT TAG")
                print('=' * 50)
    except KeyboardInterrupt:
        print('\n👋 RFID test stopped by user')
        break
    except Exception as e:
        print(f'❌ Error during RFID scan: {e}')