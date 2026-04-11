from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from datetime import datetime
from typing import List
from redis.asyncio import Redis
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, CompleteAppointmentRequest
from app.services.queue_service import QueueService


class AppointmentService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.queue_service = QueueService(db, redis)

    async def create_appointment(self, patient_id: int, data: AppointmentCreate) -> AppointmentResponse:
        result = await self.db.execute(select(Doctor).where(Doctor.id == data.doctor_id))
        doctor = result.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        if not doctor.is_available:
            raise HTTPException(status_code=400, detail="Doctor is not available")

        count_result = await self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.doctor_id == data.doctor_id,
                Appointment.status.in_([AppointmentStatus.QUEUED, AppointmentStatus.IN_PROGRESS])
            )
        )
        token_number = (count_result.scalar() or 0) + 1

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=data.doctor_id,
            token_number=token_number,
            symptoms=data.symptoms,
            status=AppointmentStatus.QUEUED,
        )
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)

        score = datetime.utcnow().timestamp()
        position = await self.queue_service.enqueue(data.doctor_id, appointment.id, score)
        appointment.queue_position = position
        await self.db.commit()

        return await self._to_response(appointment)

    async def get_patient_appointments(self, patient_id: int) -> List[AppointmentResponse]:
        result = await self.db.execute(
            select(Appointment, Doctor, User)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .join(User, Doctor.user_id == User.id)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.appointment_date.desc())
        )
        rows = result.all()
        responses = []
        for appt, doctor, user in rows:
            pos = None
            if appt.status == AppointmentStatus.QUEUED:
                pos = await self.queue_service.get_position(doctor.id, appt.id)
            resp = AppointmentResponse(
                id=appt.id,
                patient_id=appt.patient_id,
                doctor_id=appt.doctor_id,
                token_number=appt.token_number,
                status=appt.status,
                symptoms=appt.symptoms,
                notes=appt.notes,
                appointment_date=appt.appointment_date,
                completed_at=appt.completed_at,
                queue_position=pos,
                doctor_name=user.full_name,
            )
            responses.append(resp)
        return responses

    async def get_doctor_appointments(self, doctor_user_id: int) -> List[AppointmentResponse]:
        result_doctor = await self.db.execute(select(Doctor).where(Doctor.user_id == doctor_user_id))
        doctor = result_doctor.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor profile not found")

        result = await self.db.execute(
            select(Appointment, User)
            .join(User, Appointment.patient_id == User.id)
            .where(Appointment.doctor_id == doctor.id)
            .order_by(Appointment.appointment_date.desc())
        )
        rows = result.all()
        responses = []
        for appt, patient in rows:
            pos = None
            if appt.status == AppointmentStatus.QUEUED:
                pos = await self.queue_service.get_position(doctor.id, appt.id)
            resp = AppointmentResponse(
                id=appt.id,
                patient_id=appt.patient_id,
                doctor_id=appt.doctor_id,
                token_number=appt.token_number,
                status=appt.status,
                symptoms=appt.symptoms,
                notes=appt.notes,
                appointment_date=appt.appointment_date,
                completed_at=appt.completed_at,
                queue_position=pos,
                patient_name=patient.full_name,
            )
            responses.append(resp)
        return responses

    async def complete_appointment(self, doctor_user_id: int, data: CompleteAppointmentRequest) -> AppointmentResponse:
        result_doctor = await self.db.execute(select(Doctor).where(Doctor.user_id == doctor_user_id))
        doctor = result_doctor.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor profile not found")

        result = await self.db.execute(
            select(Appointment).where(
                Appointment.id == data.appointment_id,
                Appointment.doctor_id == doctor.id,
            )
        )
        appt = result.scalar_one_or_none()
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        appt.status = AppointmentStatus.COMPLETED
        appt.completed_at = datetime.utcnow()
        if data.notes:
            appt.notes = data.notes

        await self.queue_service.remove_from_queue(doctor.id, appt.id)
        await self.db.commit()
        await self.db.refresh(appt)
        return await self._to_response(appt)

    async def _to_response(self, appt: Appointment) -> AppointmentResponse:
        result_patient = await self.db.execute(select(User).where(User.id == appt.patient_id))
        patient = result_patient.scalar_one_or_none()

        result_doctor = await self.db.execute(select(Doctor).where(Doctor.id == appt.doctor_id))
        doctor = result_doctor.scalar_one_or_none()
        doctor_user = None
        if doctor:
            res = await self.db.execute(select(User).where(User.id == doctor.user_id))
            doctor_user = res.scalar_one_or_none()

        pos = None
        if appt.status == AppointmentStatus.QUEUED:
            pos = await self.queue_service.get_position(appt.doctor_id, appt.id)

        return AppointmentResponse(
            id=appt.id,
            patient_id=appt.patient_id,
            doctor_id=appt.doctor_id,
            token_number=appt.token_number,
            status=appt.status,
            symptoms=appt.symptoms,
            notes=appt.notes,
            appointment_date=appt.appointment_date,
            completed_at=appt.completed_at,
            queue_position=pos,
            doctor_name=doctor_user.full_name if doctor_user else None,
            patient_name=patient.full_name if patient else None,
        )
