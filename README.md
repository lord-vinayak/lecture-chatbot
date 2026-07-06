# Video Course Q&A Platform

A self-hosted platform where students ask questions about course videos and get accurate answers grounded exclusively in the video transcript - no hallucination, no external knowledge. Built for instructors who teach hour-long course videos and want students to get instant, trustworthy answers.

## Key Features

- **Upload & transcribe** course videos automatically via Faster-Whisper
- **Ask questions** and get answers sourced only from what was taught in the video
- **Hallucination prevention** - model explicitly refuses if the answer isn't in the transcript
- **Chat history** with source chunk transparency (see exactly which part of the transcript was used)
- **OpenAI-powered** answers via GPT-4o-mini (fast, cheap, accurate)
- **Docker-first** - single `docker-compose up` to run everything locally

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Run Locally](#run-locally)
- [Deploy to Hostinger VPS](#deploy-to-hostinger-vps)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Production Scaling Path](#production-scaling-path)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + TypeScript + Axios |
| **Backend** | Python 3.11 + FastAPI + Uvicorn |
| **Transcription** | Faster-Whisper (4x faster than standard Whisper) |
| **LLM Inference** | OpenAI API (GPT-4o-mini by default) |
| **Embeddings** | Sentence-transformers `all-MiniLM-L6-v2` (384-dim, runs locally) |
| **Database** | PostgreSQL 15 + pgvector extension |
| **ORM** | SQLAlchemy 2.0 |
| **Validation** | Pydantic v2 |
| **Orchestration** | Docker Compose |

---

## Prerequisites

### For local development (Docker)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 24+
- [Git](https://git-scm.com/)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A GPU is recommended for Whisper transcription (NVIDIA with CUDA). CPU works but is slower.

### For local development (without Docker)
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with the pgvector extension installed
- An OpenAI API key

---

## Run Locally

### Step 1: Clone the repo

```bash
git clone https://github.com/lord-vinayak/lecture-chatbot.git
cd lecture-chatbot
```

### Step 2: Set your OpenAI API key

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and set your key:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/videochat
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=base
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Step 3: Start all services

```bash
docker-compose up --build
```

This starts three containers:

| Container | What it is | Port |
|---|---|---|
| `videochat_postgres` | PostgreSQL 15 + pgvector | 5432 |
| `videochat_backend` | FastAPI backend | 8000 |
| `videochat_frontend` | React frontend | 3000 |

The database schema (tables + pgvector indexes) is applied automatically on first start.

First build takes 3-5 minutes while Docker downloads images and installs Python packages. Subsequent starts are instant.

### Step 4: Verify it's working

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

### Step 5: Open the app

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **API docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

### Without Docker (manual setup)

**Backend:**

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values

uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

**Database (manual):**

Make sure PostgreSQL is running and the pgvector extension is installed:

```sql
-- Connect as superuser
CREATE DATABASE videochat;
\c videochat
CREATE EXTENSION IF NOT EXISTS vector;
```

Then apply the schema:

```bash
psql -U postgres -d videochat -f backend/migrations/001_initial_schema.sql
```

---

## Deploy to Hostinger VPS

### What you need

- A Hostinger KVM VPS plan (KVM 2 or higher recommended - 2 vCPU, 8GB RAM minimum)
- Ubuntu 22.04 as the OS (select during VPS creation)
- Your OpenAI API key
- A domain name (optional but recommended - you can use the VPS IP directly)

> **GPU note:** With OpenAI handling LLM inference, you no longer need a GPU for answering questions. A GPU is only useful for faster Whisper transcription. For most use cases, a CPU-only VPS works fine with `WHISPER_MODEL=base`.

---

### Phase 1: Initial Server Setup

**1. SSH into your VPS**

Hostinger gives you the root password via email or the hPanel dashboard.

```bash
ssh root@YOUR_VPS_IP
```

**2. Create a non-root user**

```bash
adduser deploy
usermod -aG sudo deploy
su - deploy
```

**3. Install Docker**

```bash
# Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Compose
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow deploy user to run docker without sudo
sudo usermod -aG docker deploy

# Log out and back in for group change to take effect
exit
ssh deploy@YOUR_VPS_IP
```

**4. Verify Docker works**

```bash
docker --version
# Docker version 24.x.x

docker compose version
# Docker Compose version v2.x.x
```

---

### Phase 2: Deploy the Application

**5. Clone the repository**

```bash
cd /home/deploy
git clone https://github.com/lord-vinayak/lecture-chatbot.git
cd lecture-chatbot
```

**6. Create your production .env file**

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Set these values:

```env
DATABASE_URL=postgresql://postgres:strongpassword123@postgres:5432/videochat
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=base
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

> Use a strong postgres password - this is a production server.

**7. Update docker-compose.yml for production**

The default `docker-compose.yml` mounts source code for hot reload - fine for local dev, not for production. Create a production override:

```bash
nano docker-compose.prod.yml
```

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: strongpassword123

  backend:
    # DATABASE_URL comes from backend/.env via env_file in docker-compose.yml
    # Make sure backend/.env on the server uses strongpassword123 to match above
    volumes: []                          # don't mount source code in prod
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

  frontend:
    environment:
      REACT_APP_API_URL: http://YOUR_VPS_IP:8000
    volumes: []
    command: sh -c "npm run build && npx serve -s build -l 3000"
```

Replace `YOUR_VPS_IP` with your actual VPS IP address (or domain if you've set up DNS).

> **Important:** The postgres password in the prod override (`strongpassword123`) must match the password in your `backend/.env` `DATABASE_URL`. If you change one, change both.

**8. Build and start**

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

`-d` runs in detached (background) mode. First build takes 5-10 minutes.

**9. Check everything is running**

```bash
docker compose ps
```

Expected output:

```
NAME                    STATUS          PORTS
videochat_postgres      Up (healthy)    0.0.0.0:5432->5432/tcp
videochat_backend       Up              0.0.0.0:8000->8000/tcp
videochat_frontend      Up              0.0.0.0:3000->3000/tcp
```

**10. Test the deployment**

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

From your local machine:

```bash
curl http://YOUR_VPS_IP:8000/health
# {"status":"ok"}
```

Open `http://YOUR_VPS_IP:3000` in your browser.

---

### Phase 3: Open Firewall Ports (Hostinger hPanel)

By default, Hostinger blocks all ports except 22 (SSH). You need to open ports 3000 and 8000.

1. Log in to [hPanel](https://hpanel.hostinger.com)
2. Go to **VPS** → your server → **Firewall**
3. Add these inbound rules:

| Port | Protocol | Source | Description |
|---|---|---|---|
| 3000 | TCP | 0.0.0.0/0 | React frontend |
| 8000 | TCP | 0.0.0.0/0 | FastAPI backend |

4. Click **Save rules**

Alternatively, configure UFW directly on the server:

```bash
sudo ufw allow 22/tcp      # SSH - already open, keep it
sudo ufw allow 3000/tcp    # Frontend
sudo ufw allow 8000/tcp    # Backend API
sudo ufw enable
sudo ufw status
```

---

### Phase 4: Set Up a Domain (Optional but Recommended)

If you have a domain (e.g. `courses.yourdomain.com`), point it to your VPS and set up Nginx as a reverse proxy so both frontend and backend run on standard port 80/443.

**Install Nginx:**

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

**Create Nginx config:**

```bash
sudo nano /etc/nginx/sites-available/videochat
```

```nginx
server {
    listen 80;
    server_name courses.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Allow large video uploads (1GB max)
        client_max_body_size 1024M;
        proxy_read_timeout 300s;
    }
}
```

**Enable the site:**

```bash
sudo ln -s /etc/nginx/sites-available/videochat /etc/nginx/sites-enabled/
sudo nginx -t          # verify config is valid
sudo systemctl reload nginx
```

**Add HTTPS (free SSL via Let's Encrypt):**

```bash
sudo certbot --nginx -d courses.yourdomain.com
```

Follow the prompts. Certbot auto-renews certificates. After this, your app runs at `https://courses.yourdomain.com`.

Update `REACT_APP_API_URL` in `docker-compose.prod.yml` to use the domain:

```yaml
REACT_APP_API_URL: https://courses.yourdomain.com/api
```

Rebuild the frontend:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build frontend
```

---

### Phase 5: Keeping It Running

**Auto-restart on server reboot:**

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Create a systemd service for the app
sudo nano /etc/systemd/system/videochat.service
```

```ini
[Unit]
Description=Video Chat Q&A Platform
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/home/deploy/lecture-chatbot
ExecStart=/usr/bin/docker compose -f docker-compose.yml -f docker-compose.prod.yml up
ExecStop=/usr/bin/docker compose down
Restart=always
User=deploy

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable videochat
sudo systemctl start videochat
```

**View logs:**

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

**Update the app after a code change:**

```bash
cd /home/deploy/lecture-chatbot
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## Architecture

### How It Works

Three cleanly separated layers process every request:

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Upload & Transcription Pipeline               │
│  Video file → Faster-Whisper → transcript text          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Storage & Indexing                            │
│  transcript → chunks → embeddings → pgvector            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Chat & Inference                              │
│  question → vector search → OpenAI GPT → answer         │
└─────────────────────────────────────────────────────────┘
```

### Upload & Transcription Flow

```
Instructor uploads video
  ↓
Backend saves file to uploads/ directory
  ↓
FastAPI BackgroundTask triggers Faster-Whisper transcription
  ↓
Transcript stored in videos.transcript_text
  ↓
Transcript chunked into ~500-token windows (50-token overlap)
  ↓
Each chunk embedded via sentence-transformers (runs locally)
  ↓
Embeddings stored in transcript_chunks with pgvector
  ↓
transcription_status → "completed"
  ↓
Frontend polls /videos/{id} every 3 seconds and shows "Ready"
```

**Latency:** 2-5 minutes per hour of video on a GPU; 10-20 minutes on CPU (base model).

### Chat Query Flow

```
Student types question
  ↓
Question embedded using same sentence-transformers model (local)
  ↓
pgvector ivfflat index: SELECT TOP 3 chunks by cosine similarity
  ↓
Top 3 chunks + question sent to OpenAI GPT-4o-mini:
  system: "Answer ONLY from the transcript. Say so if not found."
  user:   "Transcript: [...chunks...]\n\nQuestion: [...]"
  ↓
GPT-4o-mini generates answer
  ↓
Answer + source chunks stored in chats table
  ↓
Response returned to frontend with expandable source chunks
```

**Total latency:** ~1 second (vector search ~100ms + OpenAI API ~700ms).

---

## API Reference

Interactive docs at `http://localhost:8000/docs` (Swagger UI).

### `POST /videos/upload`

Upload a video and start async transcription.

**Request** - multipart/form-data:

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | Video file (any format FFmpeg supports) |
| `title` | string | Yes | Display title for the video |
| `instructor_id` | UUID string | Yes | Instructor's UUID |

**Response** `200`:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Intro to Python - Lesson 1",
  "instructor_id": "...",
  "transcription_status": "pending",
  "transcript_text": null,
  "upload_date": "2026-07-06T12:00:00",
  "file_path": "uploads/550e8400....mp4"
}
```

### `GET /videos/{video_id}`

Poll transcription status. Frontend calls this every 3 seconds until status is `completed` or `failed`.

`transcription_status` values: `pending` → `completed` | `failed`

### `POST /chats/{video_id}/ask`

Ask a question. Requires `transcription_status = "completed"`.

**Query param:** `user_id` (UUID string, optional)

**Request body:**
```json
{ "question": "What is the difference between a list and a tuple?" }
```

**Response** `200`:
```json
{
  "id": "...",
  "video_id": "...",
  "user_id": "...",
  "question": "What is the difference between a list and a tuple?",
  "answer": "According to the video, lists are mutable while tuples are immutable...",
  "source_chunks": ["...transcript excerpt used...", "...another excerpt..."],
  "created_at": "2026-07-06T12:01:00"
}
```

### `GET /health`

Returns `{"status": "ok"}` when the backend is up.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/videochat` | Yes | PostgreSQL connection string |
| `OPENAI_API_KEY` | - | Yes | Your OpenAI API key (`sk-...`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | No | OpenAI model. `gpt-4o-mini` is cheapest; `gpt-4o` is most accurate |
| `WHISPER_MODEL` | `base` | No | Faster-Whisper model size (see table below) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | No | Sentence-transformers model (runs locally) |

### Frontend

| Variable | Default | Description |
|---|---|---|
| `REACT_APP_API_URL` | `http://localhost:8000` | Backend API base URL. Change to your VPS IP or domain in production. |

### Whisper Model Size Guide

| Model | Disk | RAM | Speed | Accuracy |
|---|---|---|---|---|
| `tiny` | 75MB | ~1GB | Fastest | Lower |
| `base` | 145MB | ~1GB | Fast | Good **(default)** |
| `small` | 466MB | ~2GB | Moderate | Better |
| `medium` | 1.5GB | ~5GB | Slower | Very good |
| `large` | 2.9GB | ~10GB | Slowest | Best |

### OpenAI Model Cost Guide

| Model | Cost per question (approx) | Quality |
|---|---|---|
| `gpt-4o-mini` | ~$0.001 | Good **(default)** |
| `gpt-4o` | ~$0.01 | Best |
| `gpt-3.5-turbo` | ~$0.0005 | Acceptable |

---

## Project Structure

```
lecture-chatbot/
├── backend/
│   ├── main.py                  # FastAPI app, routes, background transcription task
│   ├── models.py                # SQLAlchemy ORM (Video, TranscriptChunk, Chat)
│   ├── database.py              # Connection pool, get_db() session factory
│   ├── transcription.py         # Faster-Whisper wrapper, lazy model loading
│   ├── embeddings.py            # Chunking, sentence-transformers, cosine similarity
│   ├── llm.py                   # OpenAI API wrapper, context-only prompt
│   ├── schemas.py               # Pydantic request/response models
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment variable template
│   ├── Dockerfile               # Backend container (python:3.11-slim + ffmpeg)
│   ├── migrations/
│   │   └── 001_initial_schema.sql  # Schema + pgvector indexes (auto-applied)
│   ├── test_database.py         # ORM + connection smoke test
│   ├── test_embeddings.py       # Chunking + embedding unit tests
│   ├── test_llm.py              # OpenAI connection + QA tests
│   └── test_integration.py      # End-to-end upload → transcribe → ask flow
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root component, layout, health check, polling
│   │   ├── VideoPlayer.tsx      # Upload form, transcription status display
│   │   ├── ChatBox.tsx          # Q&A interface, message history, source chunks
│   │   ├── api.ts               # Typed Axios client (uploadVideo, askQuestion, etc.)
│   │   ├── index.tsx            # React DOM entry point
│   │   └── index.css / App.css / VideoPlayer.css / ChatBox.css
│   ├── public/index.html
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           # Local dev (with hot reload)
├── docker-compose.prod.yml      # Production overrides (create manually on server)
└── docs/
    └── DESIGN.md                # Full architecture design specification
```

---

## Database Schema

```sql
videos
├── id                   UUID PRIMARY KEY
├── title                TEXT NOT NULL
├── instructor_id        UUID NOT NULL
├── transcript_text      TEXT             -- populated after transcription
├── transcription_status VARCHAR(50)      -- 'pending' | 'completed' | 'failed'
├── upload_date          TIMESTAMP
├── file_path            TEXT NOT NULL
└── created_at           TIMESTAMP

transcript_chunks
├── id           UUID PRIMARY KEY
├── video_id     UUID → videos(id) CASCADE DELETE
├── chunk_text   TEXT NOT NULL
├── embedding    vector(384)              -- pgvector column
├── chunk_index  INT NOT NULL
└── created_at   TIMESTAMP

chats
├── id            UUID PRIMARY KEY
├── video_id      UUID → videos(id) CASCADE DELETE
├── user_id       UUID NOT NULL
├── question      TEXT NOT NULL
├── answer        TEXT
├── source_chunks JSONB
└── created_at    TIMESTAMP

-- Indexes
idx_transcript_chunks_embedding  USING ivfflat (embedding vector_cosine_ops)
idx_transcript_chunks_video_id
idx_chats_video_id
idx_chats_user_id
idx_videos_status
```

---

## Running Tests

```bash
# Exec into the running backend container
docker exec -it videochat_backend bash

# Then run any test file
python test_embeddings.py   # no external services needed
python test_llm.py          # needs OPENAI_API_KEY set
python test_database.py     # needs postgres running
python test_integration.py  # full end-to-end (place test_video.mp4 first)
```

Or locally from `backend/` with the venv activated:

```bash
python test_embeddings.py
```

---

## Troubleshooting

### Transcription stuck on "pending"

Check backend logs for errors:

```bash
docker compose logs -f backend
```

If on CPU and using `medium` or `large` model, transcription is slow (20+ minutes). Switch to `base` in `.env` and restart:

```bash
docker compose restart backend
```

### OpenAI API errors

**`AuthenticationError`** - API key is wrong or not set. Check `backend/.env`.

**`RateLimitError`** - Too many requests. The default `gpt-4o-mini` tier has generous limits; this rarely happens.

**`APIConnectionError`** - Server can't reach OpenAI (common on restricted VPS). Test connectivity:

```bash
docker exec videochat_backend curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### pgvector extension not found

Verify it's installed in the database:

```bash
docker exec videochat_postgres psql -U postgres -d videochat -c "SELECT extname FROM pg_extension;"
```

If `vector` is missing, the schema init script didn't run. Apply it manually:

```bash
docker exec -i videochat_postgres psql -U postgres -d videochat < backend/migrations/001_initial_schema.sql
```

### Ports 3000 / 8000 not accessible on VPS

Check UFW rules:

```bash
sudo ufw status
```

Check Hostinger hPanel firewall - make sure inbound TCP rules exist for ports 3000 and 8000.

### "Backend unavailable" in frontend

```bash
curl http://localhost:8000/health
```

If this fails, the backend container crashed. Check logs:

```bash
docker compose logs backend
```

### Large video uploads fail (Nginx 413 error)

Add to your Nginx server block:

```nginx
client_max_body_size 1024M;
```

Then reload Nginx:

```bash
sudo systemctl reload nginx
```

---

## Production Scaling Path

No code changes needed to scale. Only component swaps:

| Aspect | Current | Production |
|---|---|---|
| Transcription | FastAPI BackgroundTask | Celery + Redis job queue |
| Embeddings | Computed on backend | Cache in Redis |
| LLM | OpenAI gpt-4o-mini | OpenAI gpt-4o or fine-tuned model |
| Concurrency | ~50 students | Unlimited (OpenAI rate limits apply) |
| Orchestration | Docker Compose | Kubernetes or Docker Swarm |
| Storage | Local disk (`uploads/`) | S3 or compatible object storage |

---

## Known Limitations

- No authentication - demo assumes a trusted environment
- No video playback in the UI - upload + Q&A only
- Transcript chunks are sent to OpenAI per question - not suitable for highly confidential content
- Whisper may produce lower quality transcripts on noisy audio

---

## License

MIT
