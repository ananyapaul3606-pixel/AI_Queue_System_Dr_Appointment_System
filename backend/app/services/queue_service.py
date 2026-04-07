from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.models.doctor import Doctor
from app.schemas.queue import QueueResponse, QueueEntry, WaitTimeResponse

QUEUE_KEY = "queue:doctor:{doctor_id}"


class QueueService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    def _queue_key(self, doctor_id: int) -> str:
        return QUEUE_KEY.format(doctor_id=doctor_id)

    async def enqueue(self, doctor_id: int, appointment_id: int, score: float) -> int:
        key = self._queue_key(doctor_id)
        await self.redis.zadd(key, {str(appointment_id): score})
        position = await self.redis.zrank(key, str(appointment_id))
        return int(position) + 1 if position is not None else 1

    async def dequeue_next(self, doctor_id: int) -> Optional[int]:
        key = self._queue_key(doctor_id)
        items = await self.redis.zrange(key, 0, 0)
        if not items:
            return None
        appointment_id = items[0]
        await self.redis.zrem(key, appointment_id)
        return int(appointment_id)

    async def remove_from_queue(self, doctor_id: int, appointment_id: int):
        key = self._queue_key(doctor_id)
        await self.redis.zrem(key, str(appointment_id))

    async def get_queue_length(self, doctor_id: int) -> int:
        key = self._queue_key(doctor_id)
        return await self.redis.zcard(key)

    async def get_position(self, doctor_id: int, appointment_id: int) -> Optional[int]:
        key = self._queue_key(doctor_id)
        rank = await self.redis.zrank(key, str(appointment_id))
        return int(rank) + 1 if rank is not None else None

    async def get_all_in_queue(self, doctor_id: int) -> List[int]:
        key = self._queue_key(doctor_id)
        items = await self.redis.zrange(key, 0, -1)
        return [int(i) for i in items]

    async def get_queue_response(self, doctor_id: int) -> QueueResponse:
        appointment_ids = await self.get_all_in_queue(doctor_id)
        entries = []

        for idx, appt_id in enumerate(appointment_ids):
            result = await self.db.execute(
                select(Appointment, User)
                .join(User, Appointment.patient_id == User.id)
                .where(Appointment.id == appt_id)
            )
            row = result.first()
            if row:
                appt, patient = row
                entries.append(QueueEntry(
                    appointment_id=appt.id,
                    patient_id=appt.patient_id,
                    patient_name=patient.full_name,
                    token_number=appt.token_number,
                    position=idx + 1,
                    symptoms=appt.symptoms,
                ))

        return QueueResponse(
            doctor_id=doctor_id,
            queue_length=len(entries),
            entries=entries,
        )

    async def get_wait_time(self, doctor_id: int, patient_appointment_id: Optional[int] = None) -> WaitTimeResponse:
        result = await self.db.execute(select(Doctor).where(Doctor.id == doctor_id))
        doctor = result.scalar_one_or_none()
        avg_time = doctor.avg_consultation_minutes if doctor else 15.0

        queue_length = await self.get_queue_length(doctor_id)
        total_wait = queue_length * avg_time

        your_position = None
        your_wait = None
        if patient_appointment_id:
            pos = await self.get_position(doctor_id, patient_appointment_id)
            if pos:
                your_position = pos
                your_wait = pos * avg_time

        return WaitTimeResponse(
            doctor_id=doctor_id,
            queue_length=queue_length,
            avg_consultation_minutes=avg_time,
            estimated_wait_minutes=total_wait,
            your_position=your_position,
            your_wait_minutes=your_wait,
        )
