from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Upload/Video schemas
class VideoUploadRequest(BaseModel):
    title: str
    instructor_id: UUID

class VideoResponse(BaseModel):
    id: UUID
    title: str
    instructor_id: UUID
    transcription_status: str
    transcript_text: Optional[str] = None
    upload_date: datetime
    file_path: str

    class Config:
        from_attributes = True

# Chat schemas
class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    id: UUID
    video_id: UUID
    user_id: UUID
    question: str
    answer: str
    source_chunks: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    error: str
    status_code: int
