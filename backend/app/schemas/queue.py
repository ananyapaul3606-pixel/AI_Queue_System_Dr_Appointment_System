from pydantic import BaseModel
from typing import List, Optional


class QueueEntry(BaseModel):
    appointment_id: int
    patient_id: int
    patient_name: str
    token_number: int
    position: int
    symptoms: Optional[str]


class QueueResponse(BaseModel):
    doctor_id: int
    queue_length: int
    entries: List[QueueEntry]


class WaitTimeResponse(BaseModel):
    doctor_id: int
    queue_length: int
    avg_consultation_minutes: float
    estimated_wait_minutes: float
    your_position: Optional[int] = None
    your_wait_minutes: Optional[float] = None
