from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    doctor_id: int
    symptoms: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    token_number: int
    status: str
    symptoms: Optional[str]
    notes: Optional[str]
    appointment_date: datetime
    completed_at: Optional[datetime]
    queue_position: Optional[int]
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True


class CompleteAppointmentRequest(BaseModel):
    appointment_id: int
    notes: Optional[str] = None
