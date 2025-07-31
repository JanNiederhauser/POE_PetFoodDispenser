from datetime import datetime
from pydantic import BaseModel


class Pet(BaseModel):
    rfid: str
    name: str
    silo: int


class FeedingSchedule(BaseModel):
    rfid: str
    timeWindow: int
    amount: float


class FeedingCheckResponse(BaseModel):
    allowed: bool
    siloId: int
    amount: float


class Silo(BaseModel):
    id: int
    height: float
    currentHeight: float
    percentage: float


class FeedingEvent(BaseModel):
    rfid: str
    timestamp: datetime
    violatedSchedule: bool = False


class PetCreateRequest(BaseModel):
    name: str
    rfid: str
    silo: int

class ScheduleCreateRequest(BaseModel):
    rfid: str
    timeWindow: int
    amount: float

class FeedingConfirmRequest(BaseModel):
    rfid: str
    newScaleWeight: float

class RegisterPetRequest(BaseModel):
    name: str
    rfid: str
    silo: int
    timeWindow: int
    amount: float


