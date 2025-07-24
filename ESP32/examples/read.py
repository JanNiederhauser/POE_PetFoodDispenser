import mfrc522
from machine import Pin,SPI
from utime import ticks_ms

def do_read():
    spi = SPI(1, baudrate=2500000, polarity=0, phase=0)
    spi.init()
    rdr = mfrc522.MFRC522(spi=spi, gpioRst=21, gpioCs=5)

    while True:
        print("Place card")

        (stat, tag_type) = rdr.request(rdr.REQIDL)

        if stat == rdr.OK:

            (stat, raw_uid) = rdr.anticoll()

            if stat == rdr.OK:
                print("Detected")
                print("type: 0x%02x" % tag_type)
                print("uid: 0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                print("")

                if rdr.select_tag(raw_uid) == rdr.OK:

                    key = b'\xff\xff\xff\xff\xff\xff'

                    ms = ticks_ms()

                    blockArray = bytearray(16)
                    for sector in range(1, 64):
                        if rdr.auth(rdr.AUTHENT1A, sector, key, raw_uid) == rdr.OK:
                            rdr.read(sector, into=blockArray)
                            print("data@%d: %s" % (sector, blockArray))
                        else:
                            print("Auth err")
                    rdr.stop_crypto1()

                    print("Read in " + str(ticks_ms() - ms)) # took 4594 ms

                else:
                    print("Select failed")
