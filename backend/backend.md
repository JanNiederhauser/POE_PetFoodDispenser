
# Nexani Backend API

This FastAPI project powers a smart RFID-based pet feeder system. It supports pet registration, feeding schedules,
real-time food dispensing, and silo management — all accessible via RESTful endpoints and a lightweight dashboard.

---

## 📦 Features

- 🐾 RFID-based pet identification
- 🕒 Feeding schedule management and validation
- ⚖️ Silo weight tracking
- ❓ Unknown RFID event handling
- 🌐 Static dashboard for human interaction

---


## 🔧 Requirements

- Python 3.10+
- FastAPI
- Uvicorn

Install dependencies:

```bash
pip install fastapi uvicorn
```

---

## ▶️ Running the Server

```bash
uvicorn main:app --reload
```

Access the dashboard via: `http://localhost:8000/`

---

## 📘 Required Pydantic Models (models.py)

```python
class Pet(BaseModel):
    rfid: str
    name: str
    silo: int

class FeedingSchedule(BaseModel):
    rfid: str
    timeWindow: str  # format: "HH:MM-HH:MM"
    amount: float

class FeedingCheckResponse(BaseModel):
    allowed: bool
    siloId: int
    maxAmount: float

class FeedingEvent(BaseModel):
    rfid: str
    timestamp: datetime
    amountDispensed: float
    violatedSchedule: bool
```

---

## 📂 API Endpoints (with Descriptions & Types)

### 🐾 Pet Management

#### `POST /pet/create`

Register a new pet with an RFID and assign it to a silo.

**Query Parameters:**

* `name` (str)
* `rfid` (str)
* `silo` (int)

---

#### `GET /pet/get/{rfid}`

Get information about a pet.

**Path Parameter:**

* `rfid` (str)

---

#### `POST /pet/delete/{rfid}`

Delete a pet by RFID.

**Path Parameter:**

* `rfid` (str)

---

#### `GET /pet/list`

List pets, optionally limited.

**Query Parameter:**

* `limit` (int, default=10)

---

### 🕒 Feeding Schedule Management

#### `POST /schedule/create`

Create a feeding schedule for a pet.

**Request Body:** `FeedingSchedule`

---

#### `POST /schedule/update`

Update an existing feeding schedule.

**Request Body:** `FeedingSchedule`

---

#### `GET /schedule/list`

List all feeding schedules.

**Query Parameter:**

* `limit` (int, default=10)

---

### 🏠 Silo Management

#### `GET /silo/list`

List all available silos and their current stock weights.

**Query Parameter:**

* `limit` (int, default=10)

---

### 🍽️ Feeding Process

#### `POST /feeding/check/{rfid}`

Check whether a pet is currently allowed to eat based on its schedule.

**Path Parameter:**

* `rfid` (str)

**Response:**

* `allowed` (bool)
* `siloId` (int)
* `maxAmount` (float)

---

#### `POST /feeding/confirm`

Confirm that feeding has occurred, update the silo weight, and log the event.

**Query Parameters:**

* `rfid` (str)
* `newScaleWeight` (float)

---

### ❓ Unknown RFID Handling

#### `GET /dashboard/unknown-rfids`

List all unrecognized RFID scan attempts.

---

#### `POST /dashboard/unknown-rfids/dismiss/{rfid}`

Dismiss a specific unknown RFID event.

**Path Parameter:**

* `rfid` (str)

---

#### `POST /dashboard/register-pet`

Register a pet directly from an unknown RFID, with an initial schedule.

**Query Parameters:**

* `name` (str)
* `rfid` (str)
* `silo` (int)
* `timeWindow` (str) — e.g. `"07:00-10:00"`
* `amount` (float)

---

### ⚙️ Backend Health

#### `GET /backend/health`

Check service status.

**Response:**

```json
{ "status": "ok" }
```

---

#### `GET /backend/connection`

Check backend connection status.

**Response:**

```json
{ "status": "connected" }
```

---

## 🌐 Dashboard

The static dashboard is hosted at:

```
http://localhost:8000/
```

It provides:

* An overview of unknown RFID scans
* Easy pet registration interface

---

## ✍️ Author
[@Asterisk333](https://github.com/Asterisk333)
