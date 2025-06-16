import wifi

if not wifi.connect_to_wifi():
    wifi.start_config_portal()
