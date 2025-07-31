from fastapi import FastAPI, HTTPException
from datetime import datetime, time, timedelta
from fastapi.staticfiles import StaticFiles
import datasets
import models

app = FastAPI()

# ----------- Utilities -----------

def is_within_time_window(time_window: int, rfid: str) -> bool:
    # datasets.last_feedings[rfid] = datetime.now()
    # test if now is ge the time of last feeding + defined time
    return datetime.now() >= datasets.last_feedings.get(rfid, datetime.min) + timedelta(minutes=int(time_window))

def find_pet(rfid: str):
    return next((p for p in datasets.pets if p["rfid"] == rfid), None)


def find_schedule(rfid: str):
    return next((s for s in datasets.feeding_schedules if s["rfid"] == rfid), None)


def find_silo(silo_id: int):
    return next((s for s in datasets.silos if s["id"] == silo_id), None)

def convert_amount(amount: int) -> float:
    # 1s of running dispenser = 7g
    return amount / 7 * 1


# ----------- listings -----------
@app.get("/pet/list")
def list_pets(limit: int = 10):
    return datasets.pets[0:limit]


@app.get("/silo/list")
def list_silos(limit: int = 10):
    return datasets.silos[0:limit]


@app.get("/schedule/list")
def list_schedules(limit: int = 10):
    return datasets.feeding_schedules[0:limit]


# ----------- Pet Management -----------
@app.post("/pet/create")
def create_pet(name: str, rfid: str, silo: int):
    if find_pet(rfid):
        raise HTTPException(status_code=400, detail="RFID already registered")
    pet = models.Pet(rfid=rfid, name=name, silo=silo)
    datasets.pets.append(pet.model_dump())
    return {"status": "created", "pet": pet}


@app.get("/pet/get/{rfid}")
def get_pet(rfid: str):
    pet = find_pet(rfid)
    if pet:
        return pet
    raise HTTPException(status_code=404, detail="Pet not found")


@app.post("/pet/delete/{rfid}")
def delete_pet(rfid: str):
    pet = find_pet(rfid)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    datasets.pets.remove(pet)
    return {"status": "deleted"}


# ----------- Feeding Schedule Management -----------

# DONE rework schedule dataset and logic to allow for intervals and grams

@app.post("/schedule/create")
def create_schedule(schedule: models.FeedingSchedule):
    if find_schedule(schedule.rfid):
        raise HTTPException(status_code=400, detail="Schedule already exists")
    datasets.feeding_schedules.append(schedule.model_dump())
    return {"status": "created", "schedule": schedule}


@app.post("/schedule/update")
def update_schedule(schedule: models.FeedingSchedule):
    for idx, _ in enumerate(datasets.feeding_schedules):
        if _["rfid"] == schedule.rfid:
            datasets.feeding_schedules[idx] = schedule.model_dump()
            return {"status": "updated", "schedule": schedule}
    raise HTTPException(status_code=404, detail="Schedule not found")


# ----------- Feeding Logic -----------

@app.post("/feeding/check/{rfid}")
def feeding_check(rfid: str):

    pet = find_pet(rfid)
    if not pet:
        datasets.unknown_rfid_events.append({"rfid": rfid, "timestamp": datetime.now()})
        raise HTTPException(status_code=404, detail="Pet not found, added to unknown list")

    sched = find_schedule(rfid)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    # DONE rework schedule system so its 30min 100g == cat can enter every 30min and get 100g per 30min
    # reworked is_within_time_window to account for minute differences instead of time windows
    allowed = is_within_time_window(sched["timeWindow"],rfid)
    return models.FeedingCheckResponse(
        allowed=allowed,
        siloId=pet["silo"], # 1 = left, 2 = right
        # DONE give brrrr data on how much food can be dispensed
        amount=convert_amount(sched["amount"]) # in seconds
    )


@app.post("/feeding/confirm")
def feeding_confirm(rfid: str, newScaleWeight: float, currentHeight: float):
    pet = find_pet(rfid)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    silo = find_silo(pet["silo"])
    if not silo:
        raise HTTPException(status_code=404, detail="Silo not found")

    sched = find_schedule(rfid)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")

    silo["percentage"] =  100 - currentHeight * 100 / silo["height"]

    silo["stockWeight"] = newScaleWeight
    datasets.last_feedings[rfid] = datetime.now()

    event = models.FeedingEvent(
        rfid=rfid,
        timestamp=datetime.now(),
    )

    return {"status": "ok"} # basically not needed lol | , "event": event}


# ----------- Unknown RFID Handling -----------

@app.get("/dashboard/unknown-rfids")
def list_unknown_rfid():
    return datasets.unknown_rfid_events


@app.post("/dashboard/unknown-rfids/dismiss/{rfid}")
def dismiss_unknown_rfid(rfid: str):
    datasets.unknown_rfid_events = [
        e for e in datasets.unknown_rfid_events if e["rfid"] != rfid
    ]
    return {"status": "dismissed"}


@app.post("/dashboard/register-pet")
def register_pet_with_schedule(
        name: str,
        rfid: str,
        silo: int,
        timeWindow: str,
        amount: int
):
    if find_pet(rfid):
        raise HTTPException(status_code=400, detail="Pet already exists")

    pet = models.Pet(rfid=rfid, name=name, silo=silo)
    schedule = models.FeedingSchedule(rfid=rfid, timeWindow=timeWindow, amount=amount)

    datasets.pets.append(pet.model_dump())
    datasets.feeding_schedules.append(schedule.model_dump())

    datasets.unknown_rfid_events = [
        e for e in datasets.unknown_rfid_events if e["rfid"] != rfid
    ]

    return {"status": "registered", "pet": pet, "schedule": schedule}


# ----------- Backend Health -----------

@app.get("/backend/health")
def health():
    return {"status": "ok"}

# ------------ Dashboard mount -----------

app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
