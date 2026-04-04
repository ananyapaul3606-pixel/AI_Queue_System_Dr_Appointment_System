from pydantic import BaseModel
from typing import Optional


class DoctorCreate(BaseModel):
    specialization: str
    qualification: str
    experience_years: int = 0
    avg_consultation_minutes: float = 15.0
    consultation_fee: float = 500.0
    bio: Optional[str] = None
    available_from: str = "09:00"
    available_to: str = "17:00"


class DoctorUpdate(BaseModel):
    avg_consultation_minutes: Optional[float] = None
    consultation_fee: Optional[float] = None
    bio: Optional[str] = None
    available_from: Optional[str] = None
    available_to: Optional[str] = None
    is_available: Optional[bool] = None


class DoctorResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    specialization: str
    qualification: str
    experience_years: int
    avg_consultation_minutes: float
    consultation_fee: float
    bio: Optional[str]
    available_from: str
    available_to: str
    is_available: bool
    rating: float

    class Config:
        from_attributes = True
