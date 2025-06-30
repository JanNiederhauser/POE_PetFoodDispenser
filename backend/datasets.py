from datetime import datetime, timedelta

pets = [
    {
        "rfid": "123",
        "name": "Michi",
        "silo": 1
    },
    {
        "rfid": "666",
        "name": "momo",
        "silo": 2
    }
]

silos = [
    {
        "id": 1,
        "stockWeight": 12.6
    },
    {
        "id": 2,
        "stockWeight": 5.3
    }
]

feeding_schedules = [
    {
        "rfid": "123",
        "timeWindow": "08:00-20:00",
        "amount": 0.5
    }
]


# Tracks last feeding time per RFID
last_feedings = {}

# Tracks unknown rfids
# each entry: {"rfid": str, "timestamp": datetime}
unknown_rfid_events = [{"rfid": "123AAAAAAA", "timestamp": "heute"}]

