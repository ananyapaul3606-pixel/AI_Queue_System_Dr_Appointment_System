from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class AppointmentStatus:
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    token_number = Column(Integer, nullable=False)
    status = Column(String(50), default=AppointmentStatus.QUEUED)
    symptoms = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    appointment_date = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    queue_position = Column(Integer, nullable=True)

    patient = relationship("User", back_populates="appointments", foreign_keys=[patient_id])
    doctor = relationship("Doctor", back_populates="appointments")
