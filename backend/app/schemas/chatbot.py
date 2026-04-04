from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    patient_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    action: Optional[str] = None
    action_data: Optional[dict] = None
