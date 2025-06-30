import requests

BASE_URL = "http://localhost:8000"  # adjust if deployed

# ----------------------
# 1. Create Pet
# ----------------------
res = requests.post(
    f"{BASE_URL}/pet/create",
    params={"name": "Mochi", "rfid": "456", "silo": 2}
)
print("Create Pet:", res.json())

# ----------------------
# 2. Create Feeding Schedule
# ----------------------
res = requests.post(
    f"{BASE_URL}/schedule/create",
    json={
        "rfid": "456",
        "timeWindow": "06:00-18:00",
        "amount": 0.6
    }
)
print("Create Schedule:", res.json())

# ----------------------
# 3. Feeding Check (RFID scanned)
# ----------------------
res = requests.post(f"{BASE_URL}/feeding/check/456")
print("Feeding Check:", res.json())

# ----------------------
# 4. Feeding Confirmation (scale data after feeding)
# Let's say old weight was 5.3, new weight is 4.8 => dispensed 0.5
res = requests.post(
    f"{BASE_URL}/feeding/confirm",
    params={"rfid": "456", "newScaleWeight": 4.8}
)
print("Feeding Confirm:", res.json())

# ----------------------
# 5. Update Schedule
# ----------------------
res = requests.post(
    f"{BASE_URL}/schedule/update",
    json={
        "rfid": "456",
        "timeWindow": "07:00-20:00",
        "amount": 0.8
    }
)
print("Update Schedule:", res.json())

# ----------------------
# 6. Trigger unknown RFID
# ----------------------
res = requests.post(f"{BASE_URL}/feeding/check/999")
print("Unknown RFID Check:", res.status_code, res.text)

# ----------------------
# 7. List Unknown RFIDs
# ----------------------
res = requests.get(f"{BASE_URL}/dashboard/unknown-rfids")
print("Unknown RFID Events:", res.json())

# ----------------------
# 8. Register Unknown Pet from Dashboard
# ----------------------
res = requests.post(
    f"{BASE_URL}/dashboard/register-pet",
    params={
        "name": "Nala",
        "rfid": "999",
        "silo": 1,
        "timeWindow": "08:00-22:00",
        "amount": 0.4
    }
)
print("Register Unknown Pet:", res.json())

# ----------------------
# 9. Dismiss Unknown RFID
# ----------------------
res = requests.post(f"{BASE_URL}/dashboard/unknown-rfids/dismiss/999")
print("Dismiss RFID:", res.json())

# ----------------------
# 10. Health Check
# ----------------------
res = requests.get(f"{BASE_URL}/backend/health")
print("Health Check:", res.json())