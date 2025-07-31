from datetime import datetime
from pydantic import BaseModel


class Pet(BaseModel):
    rfid: str
    name: str
    silo: int


class FeedingSchedule(BaseModel):
    rfid: str
    timeWindow: str  # e.g., "08:00-20:00"
    amount: float     # max amount per feeding


class FeedingCheckResponse(BaseModel):
    allowed: bool
    siloId: int
    amount: float


class Silo(BaseModel):
    id: int
    stockWeight: float


class FeedingEvent(BaseModel):
    rfid: str
    timestamp: datetime
    violatedSchedule: bool = False


class PetCreateRequest(BaseModel):
    name: str
    rfid: str
    silo: int
    profile_picture: str | None = None

class ScheduleCreateRequest(BaseModel):
    rfid: str
    timeWindow: str
    amount: float

class FeedingConfirmRequest(BaseModel):
    rfid: str
    newScaleWeight: float


