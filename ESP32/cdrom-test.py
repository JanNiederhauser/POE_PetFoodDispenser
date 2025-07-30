# CD-ROM Laufwerkssteuerung
CD1_1_CTRL = Pin(11, Pin.OUT)
CD1_2_CTRL = Pin(2, Pin.OUT)
CD2_1_CTRL = Pin(10, Pin.OUT)
CD2_2_CTRL = Pin(8, Pin.OUT)
CD1_1_CTRL(1)
CD1_2_CTRL(1)
CD2_1_CTRL(1)
CD2_2_CTRL(1)
time.sleep(0.2)
CD_POWER = Pin(3, Pin.OUT)
CD_POWER(1)  # CD-ROM Laufwerk ausschalten

# CD 1 
CD1_1_CTRL(0)
CD1_2_CTRL(0)
time.sleep(0.2)
CD_POWER(0)  # CD-ROM Laufwerk einschalten
time.sleep(1.5)
CD_POWER(1)  # CD-ROM Laufwerk ausschalten
CD1_1_CTRL(1)
CD1_2_CTRL(1)

# CD 2
CD2_1_CTRL(0)
CD2_2_CTRL(0)
time.sleep(0.2)
CD_POWER(0)  # CD-ROM Laufwerk einschalten
time.sleep(1.5)
CD_POWER(1)  # CD-ROM Laufwerk ausschalten
CD2_1_CTRL(1)
CD2_2_CTRL(1)





CD_POWER(0)  # CD-ROM Laufwerk ausschalten
time.sleep(3)

CD_POWER(1)  # CD-ROM Laufwerk einschalten