from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.deps import get_db, get_current_user
from app.db.session import redis_client
from app.models.user import User
from app.schemas.queue import QueueResponse, WaitTimeResponse
from app.services.queue_service import QueueService
from app.services.appointment_service import AppointmentService
from app.models.appointment import Appointment, AppointmentStatus
from sqlalchemy import select

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/{doctor_id}", response_model=QueueResponse)
async def get_queue(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = QueueService(db, redis_client)
    return await service.get_queue_response(doctor_id)


@router.get("/wait-time/{doctor_id}", response_model=WaitTimeResponse)
async def get_wait_time(
    doctor_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = QueueService(db, redis_client)
    result = await db.execute(
        select(Appointment).where(
            Appointment.patient_id == current_user.id,
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatus.QUEUED,
        )
    )
    appt = result.scalar_one_or_none()
    appt_id = appt.id if appt else None
    return await service.get_wait_time(doctor_id, appt_id)
