from fastapi import FastAPI, File, Form, UploadFile, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv

from database import get_db, get_db_context
from models import Video, TranscriptChunk, Chat
from schemas import VideoResponse, ChatRequest, ChatResponse
from transcription import transcribe_video
from embeddings import chunk_transcript, embed_texts
from llm import answer_question

load_dotenv()

app = FastAPI(title="Video Chat Q&A Platform")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Serve uploaded video files directly (supports Range requests for seeking)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# --- Background transcription task ---
def transcribe_and_store(video_id: uuid.UUID, file_path: str):
    """Background task: transcribe video and store transcript + chunks"""
    try:
        with get_db_context() as db:
            video = db.query(Video).filter(Video.id == video_id).first()

            def update_progress(percent: int):
                video.transcription_progress = percent
                db.commit()

            # Transcribe
            transcript = transcribe_video(file_path, on_progress=update_progress)

            # Store transcript
            video.transcript_text = transcript
            video.transcription_status = "completed"
            video.transcription_progress = 100
            db.commit()

            # Chunk and embed
            chunks = chunk_transcript(transcript, chunk_size=500, overlap=50)
            embeddings = embed_texts(chunks)

            # Store chunks
            for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_record = TranscriptChunk(
                    video_id=video_id,
                    chunk_text=chunk_text,
                    embedding=embedding,
                    chunk_index=idx
                )
                db.add(chunk_record)

            db.commit()
            print(f"✓ Transcription complete for video {video_id}: {len(chunks)} chunks")

    except Exception as e:
        with get_db_context() as db:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video:
                video.transcription_status = "failed"
                db.commit()
        print(f"✗ Transcription failed for video {video_id}: {str(e)}")

# --- Endpoints ---

@app.get("/videos", response_model=List[VideoResponse])
async def list_videos(db: Session = Depends(get_db)):
    """List all uploaded videos, most recent first"""
    return db.query(Video).order_by(Video.upload_date.desc()).all()

@app.post("/videos/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    instructor_id: str = Form(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Upload a video and start transcription in background"""

    if not title or not instructor_id:
        raise HTTPException(status_code=400, detail="title and instructor_id required")

    try:
        instructor_uuid = uuid.UUID(instructor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid instructor_id UUID")

    # Save file
    video_id = uuid.uuid4()
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{video_id}{file_extension}"

    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    # Create video record
    video = Video(
        id=video_id,
        title=title,
        instructor_id=instructor_uuid,
        file_path=str(file_path),
        transcription_status="pending"
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Start transcription in background
    background_tasks.add_task(transcribe_and_store, video_id, str(file_path))

    return video

@app.get("/videos/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db: Session = Depends(get_db)):
    """Get video details and transcription status"""
    try:
        vid_uuid = uuid.UUID(video_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid video_id UUID")

    video = db.query(Video).filter(Video.id == vid_uuid).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video

@app.post("/chats/{video_id}/ask", response_model=ChatResponse)
async def ask_question(
    video_id: str,
    request: ChatRequest,
    user_id: str = "anonymous",
    db: Session = Depends(get_db)
):
    """Ask a question about a video transcript"""

    try:
        vid_uuid = uuid.UUID(video_id)
        user_uuid = uuid.UUID(user_id) if user_id != "anonymous" else uuid.uuid4()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Check video exists and is transcribed
    video = db.query(Video).filter(Video.id == vid_uuid).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.transcription_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Video not ready (status: {video.transcription_status})"
        )

    from embeddings import embed_text

    question_embedding = embed_text(request.question)
    similar_rows = (
        db.query(TranscriptChunk.chunk_text)
        .filter(TranscriptChunk.video_id == vid_uuid)
        .order_by(TranscriptChunk.embedding.cosine_distance(question_embedding))
        .limit(3)
        .all()
    )
    similar_chunks = [r.chunk_text for r in similar_rows]

    if not similar_chunks:
        raise HTTPException(status_code=400, detail="No transcript chunks found")

    # Generate answer
    answer_text = answer_question(request.question, similar_chunks)

    # Store in chat history
    chat = Chat(
        id=uuid.uuid4(),
        video_id=vid_uuid,
        user_id=user_uuid,
        question=request.question,
        answer=answer_text,
        source_chunks=similar_chunks
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
