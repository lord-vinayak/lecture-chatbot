from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# --- Background transcription task ---
def transcribe_and_store(video_id: uuid.UUID, file_path: str):
    """Background task: transcribe video and store transcript + chunks"""
    try:
        with get_db_context() as db:
            video = db.query(Video).filter(Video.id == video_id).first()

            # Transcribe
            transcript = transcribe_video(file_path)

            # Store transcript
            video.transcript_text = transcript
            video.transcription_status = "completed"
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
            video.transcription_status = "failed"
            db.commit()
        print(f"✗ Transcription failed for video {video_id}: {str(e)}")

# --- Endpoints ---

@app.post("/videos/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = None,
    instructor_id: str = None,
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

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

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

    # Get transcript chunks
    chunks = db.query(TranscriptChunk).filter(
        TranscriptChunk.video_id == vid_uuid
    ).all()

    if not chunks:
        raise HTTPException(status_code=400, detail="No transcript chunks found")

    # Find relevant chunks via vector search
    from embeddings import embed_text, find_similar_chunks

    question_embedding = embed_text(request.question)
    chunk_embeddings = [(c.chunk_text, c.embedding) for c in chunks]
    similar_chunks = find_similar_chunks(question_embedding, chunk_embeddings, top_k=3)

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
