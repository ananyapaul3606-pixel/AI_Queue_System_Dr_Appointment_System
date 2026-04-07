from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import List
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse


class DoctorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_doctor_profile(self, user_id: int, data: DoctorCreate) -> DoctorResponse:
        result = await self.db.execute(select(Doctor).where(Doctor.user_id == user_id))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Doctor profile already exists")

        doctor = Doctor(user_id=user_id, **data.model_dump())
        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return await self._to_response(doctor)

    async def get_all_doctors(self) -> List[DoctorResponse]:
        result = await self.db.execute(
            select(Doctor, User).join(User, Doctor.user_id == User.id)
        )
        rows = result.all()
        responses = []
        for doctor, user in rows:
            responses.append(self._build_response(doctor, user))
        return responses

    async def get_doctor_by_id(self, doctor_id: int) -> DoctorResponse:
        result = await self.db.execute(
            select(Doctor, User)
            .join(User, Doctor.user_id == User.id)
            .where(Doctor.id == doctor_id)
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return self._build_response(row[0], row[1])

    async def update_doctor(self, user_id: int, data: DoctorUpdate) -> DoctorResponse:
        result = await self.db.execute(select(Doctor).where(Doctor.user_id == user_id))
        doctor = result.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor profile not found")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(doctor, field, value)

        await self.db.commit()
        await self.db.refresh(doctor)
        return await self._to_response(doctor)

    def _build_response(self, doctor: Doctor, user: User) -> DoctorResponse:
        return DoctorResponse(
            id=doctor.id,
            user_id=doctor.user_id,
            full_name=user.full_name,
            email=user.email,
            specialization=doctor.specialization,
            qualification=doctor.qualification,
            experience_years=doctor.experience_years,
            avg_consultation_minutes=doctor.avg_consultation_minutes,
            consultation_fee=doctor.consultation_fee,
            bio=doctor.bio,
            available_from=doctor.available_from,
            available_to=doctor.available_to,
            is_available=doctor.is_available,
            rating=doctor.rating,
        )

    async def _to_response(self, doctor: Doctor) -> DoctorResponse:
        result = await self.db.execute(select(User).where(User.id == doctor.user_id))
        user = result.scalar_one()
        return self._build_response(doctor, user)
