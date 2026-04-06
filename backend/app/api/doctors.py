from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.deps import get_db, get_current_user, get_current_doctor_user
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=List[DoctorResponse])
async def list_doctors(db: AsyncSession = Depends(get_db)):
    service = DoctorService(db)
    return await service.get_all_doctors()


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    service = DoctorService(db)
    return await service.get_doctor_by_id(doctor_id)


@router.post("/profile", response_model=DoctorResponse)
async def create_profile(
    data: DoctorCreate,
    current_user: User = Depends(get_current_doctor_user),
    db: AsyncSession = Depends(get_db),
):
    service = DoctorService(db)
    return await service.create_doctor_profile(current_user.id, data)


@router.patch("/profile", response_model=DoctorResponse)
async def update_profile(
    data: DoctorUpdate,
    current_user: User = Depends(get_current_doctor_user),
    db: AsyncSession = Depends(get_db),
):
    service = DoctorService(db)
    return await service.update_doctor(current_user.id, data)
