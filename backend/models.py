from sqlalchemy import Column, String, Text, DateTime, Integer, TIMESTAMP, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    instructor_id = Column(UUID(as_uuid=True), nullable=False)
    transcript_text = Column(Text)
    transcription_status = Column(String(50), default='pending')
    transcription_progress = Column(Integer, nullable=False, default=0)
    upload_date = Column(TIMESTAMP, default=datetime.utcnow)
    file_path = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(384))
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    source_chunks = Column(JSONB)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
