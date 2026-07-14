from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Upload/Video schemas
class VideoUploadRequest(BaseModel):
    title: str
    instructor_id: UUID

class YoutubeVideoRequest(BaseModel):
    title: str
    instructor_id: UUID
    youtube_url: str

class VideoResponse(BaseModel):
    id: UUID
    title: str
    instructor_id: UUID
    transcription_status: str
    transcription_progress: int = 0
    transcript_text: Optional[str] = None
    upload_date: datetime
    file_path: Optional[str] = None
    source_type: str
    youtube_url: Optional[str] = None

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
