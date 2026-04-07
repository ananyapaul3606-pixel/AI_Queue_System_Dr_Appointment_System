from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Time
from sqlalchemy.orm import relationship
from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialization = Column(String(255), nullable=False)
    qualification = Column(String(255), nullable=False)
    experience_years = Column(Integer, default=0)
    avg_consultation_minutes = Column(Float, default=15.0)
    consultation_fee = Column(Float, default=500.0)
    bio = Column(Text, nullable=True)
    available_from = Column(String(10), default="09:00")
    available_to = Column(String(10), default="17:00")
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=4.5)

    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")
