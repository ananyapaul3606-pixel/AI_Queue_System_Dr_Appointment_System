from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services.chatbot_service import ChatbotService
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["chatbot"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not settings.NVIDIA_API_KEY or settings.NVIDIA_API_KEY == "your-nvidia-api-key-here":
        raise HTTPException(status_code=503, detail="Chatbot not configured. Set NVIDIA_API_KEY in backend/.env")

    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Chatbot is available for patients only")

    service = ChatbotService(db, patient_id=current_user.id)
    result = await service.chat([m.model_dump() for m in request.messages])
    return ChatResponse(**result)
