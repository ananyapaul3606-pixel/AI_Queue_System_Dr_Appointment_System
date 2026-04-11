from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.deps import get_db, get_current_user, get_current_doctor_user
from app.db.session import redis_client
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, CompleteAppointmentRequest
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse)
async def book_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db, redis_client)
    return await service.create_appointment(current_user.id, data)


@router.get("/my", response_model=List[AppointmentResponse])
async def my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db, redis_client)
    return await service.get_patient_appointments(current_user.id)


@router.get("/doctor/all", response_model=List[AppointmentResponse])
async def doctor_appointments(
    current_user: User = Depends(get_current_doctor_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db, redis_client)
    return await service.get_doctor_appointments(current_user.id)


@router.post("/complete", response_model=AppointmentResponse)
async def complete_appointment(
    data: CompleteAppointmentRequest,
    current_user: User = Depends(get_current_doctor_user),
    db: AsyncSession = Depends(get_db),
):
    service = AppointmentService(db, redis_client)
    return await service.complete_appointment(current_user.id, data)
