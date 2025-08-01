from datetime import datetime, timedelta

pets = []

silos = [
    {
        "id": 1,
        "height": 23,
        "currentHeight": 23,
        "percentage": 100,
    },
    {
        "id": 2,
        "height": 23,
        "currentHeight": 23,
        "percentage": 100,
    }
]

feeding_schedules = []


# Tracks last feeding time per RFID
last_feedings = {}

# Tracks unknown rfids
# each entry: {"rfid": str, "timestamp": datetime}
unknown_rfid_events = []

