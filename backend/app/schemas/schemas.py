from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
import datetime as dt


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str = Field(..., min_length=1)


class Citation(BaseModel):
    document: str
    page: int
    snippet: str


class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    reply: str
    agent: str
    confidence: Optional[float] = None
    citations: List[Citation] = []
    booking_state: Optional[str] = None
    meta: Dict[str, Any] = {}


class AppointmentCreate(BaseModel):
    user_id: Optional[str] = None
    full_name: str
    email: str
    phone: str
    date_text: str  # natural language, will be parsed


class AppointmentOut(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    phone: str
    appointment_date: str
    original_date_text: Optional[str] = None
    status: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: str
    filename: str
    num_pages: int
    num_chunks: int
    size_bytes: int
    status: str
    uploaded_at: dt.datetime

    class Config:
        from_attributes = True


class AnalyticsSummary(BaseModel):
    total_chats: int
    total_appointments: int
    total_users: int
    total_documents: int
    agent_usage: Dict[str, int]
    avg_response_time_ms: float
