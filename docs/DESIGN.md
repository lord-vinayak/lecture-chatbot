# Video Chat Q&A Platform - Design Specification

**Date:** 2026-07-05  
**Status:** Approved for Implementation  
**Approach:** Hybrid (Demo → Production Path)

---

## Problem Statement

Instructors teach 1-hour course videos. Students need to ask questions about the content and receive accurate answers based only on what was taught in the video - no hallucination, no external facts. The system must be cost-minimal and deployable to Hetzner/Hostinger.

---

## Architecture Overview

Three cleanly separated layers enable both demo simplicity and production scaling:

1. **Upload & Transcription Pipeline** - Videos uploaded, transcribed asynchronously, stored
2. **Storage & Indexing** - Transcripts chunked and embedded for fast retrieval
3. **Chat & Inference** - Questions answered via vector search + local LLM

This separation means scaling later requires only swapping components (Ollama → vLLM, single instance → async queue) without rewriting core logic.

---

## Technology Stack

### Demo Phase
- **Frontend:** React (simple chat UI + video player left sidebar)
- **Backend:** Python FastAPI
- **Transcription:** Faster-Whisper (4x faster than standard Whisper, identical accuracy)
- **LLM & Inference:** Ollama + Llama 3.3 8B (runs locally on GPU)
- **Database:** Postgres + pgvector extension (embeddings stored co-located with text)
- **Embeddings:** Sentence-transformers or Ollama's built-in embedding model
- **Hosting:** Hetzner or Hostinger (with GPU allocation, e.g., RTX 3090 or better)

### Production Scaling (no code changes needed)
- Transcription: Add Celery/Bull job queue for async processing
- Inference: Replace Ollama with vLLM or SGLang for concurrent request handling
- Caching: Add Redis for embedding cache and response caching
- Orchestration: Docker Compose (demo) → Kubernetes (production)

---

## Data Model

```sql
-- Videos table
CREATE TABLE videos (
  id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  instructor_id UUID NOT NULL,
  transcript_text TEXT,
  transcription_status VARCHAR (pending|completed|failed),
  upload_date TIMESTAMP,
  file_path TEXT
);

-- Transcript chunks with embeddings
CREATE TABLE transcript_chunks (
  id UUID PRIMARY KEY,
  video_id UUID REFERENCES videos(id),
  chunk_text TEXT NOT NULL,
  embedding vector(384),  -- pgvector embedding
  chunk_index INT,
  created_at TIMESTAMP
);

-- Chat history
CREATE TABLE chats (
  id UUID PRIMARY KEY,
  video_id UUID REFERENCES videos(id),
  user_id UUID NOT NULL,
  question TEXT NOT NULL,
  answer TEXT,
  source_chunks JSONB,  -- which transcript chunks were used
  created_at TIMESTAMP
);

-- Create indexes for fast search
CREATE INDEX ON transcript_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## Data Flow

### 1. Video Upload & Transcription

```
Instructor uploads video
  ↓
Backend saves file to disk/S3
  ↓
Trigger Faster-Whisper transcription (async in demo, job queue in production)
  ↓
Whisper outputs: full transcript + timestamps
  ↓
Store transcript in videos.transcript_text
  ↓
Mark transcription_status = "completed"
  ↓
UI notifies instructor: "Ready for students"
```

**Latency:** 2-5 minutes per hour of video (depends on GPU, typically 1-3 hours for a 1-hour video with a mid-range GPU).

### 2. Chunking & Embedding (Automatic)

```
On transcription completion:
  ↓
Split transcript into ~500-token chunks (with 50-token overlap for context)
  ↓
For each chunk:
  - Embed using sentence-transformers or Ollama embedding model
  - Store in transcript_chunks table (chunk_text, embedding, video_id)
  ↓
Create vector index on embeddings column for fast search
```

**Latency:** <5 seconds total for a 1-hour video (embedding is fast).

### 3. Chat Query Flow

```
Student asks question in chat
  ↓
Embed question using same embedding model as transcript chunks
  ↓
Vector search: SELECT TOP 3 transcript_chunks ORDER BY embedding <-> question_embedding
  ↓
Retrieve top 3 similar chunks (nearest neighbors in vector space)
  ↓
Pass to Ollama Llama 3.3 8B with prompt:
  "Based ONLY on this transcript content, answer the question. If not in content, say so.
   Transcript: [chunks]
   Question: [student question]"
  ↓
Model generates answer
  ↓
Return answer to student
  ↓
Store in chats table for history
```

**Total latency:** 1-3 seconds
- Vector search: ~500ms
- LLM inference: ~1-2.5s (depends on answer length and GPU)

---

## Error Handling & Edge Cases

### Transcription Failures
- If Faster-Whisper fails (corrupted audio, unsupported format):
  - Mark video as `transcription_status = "failed"`
  - Instructor sees error message: "Transcription failed - check audio quality"
  - Student sees: "This video is still being processed"
  - Instructor can re-upload after fixing audio

### LLM Response Failures
- If Ollama times out or crashes:
  - Return graceful error to student: "Unable to process your question right now"
  - Fallback: return raw transcript chunk text without synthesis
  - Student gets *something* useful rather than nothing
  - Log error for ops team

### Vector Search Miss (Question Not in Video)
- If no similar chunks found (very different question):
  - LLM runs with empty context
  - Model trained via prompt to say: "I couldn't find that in the video"
  - This is *desired* behavior (prevent hallucination)

### Concurrent Users Under Load
- Ollama handles 2-4 concurrent requests on a mid-range GPU
- Requests queue naturally; response time degrades gracefully
- Demo can handle ~10 concurrent students
- Production scaling (vLLM): 20+ concurrent requests without degradation

---

## Demo Success Criteria

1. **Upload a 10-minute test video** → Transcription completes in <5 minutes
2. **Ask question directly answered in video** → Get correct answer from transcript
3. **Ask question NOT in video** → Model says "not in video" (doesn't hallucinate)
4. **3 concurrent students** → All get responses within 3-5 seconds

Test script:
- Upload test video
- Wait for transcription
- Ask 3 test questions (1 answerable, 1 unanswerable, 1 edge case)
- Verify responses
- Report pass/fail

---

## Demo → Production Scaling

No code changes needed. Only component swaps:

| Aspect | Demo | Production |
|--------|------|-----------|
| Transcription | Synchronous Faster-Whisper | Celery job queue + async processing |
| Inference | Single Ollama instance | vLLM with load balancing |
| Caching | None | Redis for embeddings + responses |
| Concurrency | ~10 students | 50+ concurrent students |
| Orchestration | Single server | Kubernetes or Docker Compose |

---

## File Structure

```
videochat/
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── transcription.py        # Faster-Whisper wrapper
│   ├── embeddings.py           # Embedding + vector search
│   ├── llm.py                  # Ollama inference wrapper
│   ├── models.py               # SQLAlchemy ORM models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main app component
│   │   ├── VideoPlayer.tsx     # Left sidebar video player
│   │   ├── ChatBox.tsx         # Right sidebar chat
│   │   └── index.css
│   └── package.json
├── docs/
│   └── DESIGN.md               # This file
└── docker-compose.yml          # Local dev setup
```

---

## Known Limitations & Future Work

1. **Single-instance demo** - Not load-balanced yet (production path uses vLLM)
2. **No video library sidebar** - Will add collapsible library in UI
3. **No authentication** - Demo assumes trusted environment
4. **No cost tracking** - Will add later if running on cloud infra
5. **Whisper hallucination on audio noise** - Mitigated by prompt ("answer from transcript only")

---

## Success Metrics

- **Response latency:** 1-3 seconds per question ✓
- **Transcription accuracy:** Whisper's baseline (95%+ for clean audio)
- **Hallucination rate:** <5% (via prompt engineering + context-only answers)
- **Cost:** $0/month API fees (all open-source, GPU cost is capex not opex)

