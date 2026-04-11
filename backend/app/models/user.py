from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import enum


class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.patient, nullable=False)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    appointments = relationship("Appointment", back_populates="patient", foreign_keys="Appointment.patient_id")
