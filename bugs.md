# Bug Report — videochat — 2026-07-06

## Summary
- Critical: 0 open, 3 fixed
- Intermediate: 0 open, 5 fixed
- Normal: 3 open, 0 fixed

---

## 🔴 Critical

### BUG-001: openai 1.6.1 passes `proxies` to httpx which dropped it in >=0.28.0
- **File:** `backend/requirements.txt:9`
- **Issue:** `openai==1.6.1` internally calls `httpx.Client(proxies=...)`. httpx removed that parameter in v0.28.0. pip resolves httpx to the latest version, which causes the crash at startup every time.
- **Trigger:** `docker compose up --build` — backend crashes immediately before serving any request.
- **Impact:** Backend never starts. App is completely dead.
- **Suggested Fix:** Bump openai to `>=1.52.0` (the version that removed the proxies call). Change `openai==1.6.1` → `openai>=1.52.0` in requirements.txt.
- **Status:** Fixed 2026-07-06

### BUG-002: Whisper model hardcoded to CUDA — crashes on CPU-only VPS
- **File:** `backend/transcription.py:14`
- **Issue:** `WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")` always requests a GPU. Hostinger KVM VPS has no GPU.
- **Trigger:** Any video upload on a CPU-only machine (including your Hostinger VPS).
- **Impact:** Background transcription crashes immediately; every video stays permanently `pending` or flips to `failed`. Core feature is broken in production.
- **Suggested Fix:** Auto-detect via `ctranslate2.get_cuda_device_count()`, fall back to `device="cpu", compute_type="int8"`.
- **Status:** Fixed 2026-07-06

### BUG-003: `allow_origins=["*"]` combined with `allow_credentials=True` — CORS blocked by all browsers
- **File:** `backend/main.py:21-27`
- **Issue:** The CORS spec forbids wildcard origin with credentials. Browsers will reject every credentialed request with a CORS error.
- **Trigger:** Any frontend request from a browser in production (anything but localhost).
- **Impact:** Frontend cannot communicate with the backend in production. All API calls fail silently.
- **Suggested Fix:** Set `allow_credentials=False` (no cookies/auth headers are used in this app).
- **Status:** Fixed 2026-07-06

---

## 🟡 Intermediate

### BUG-004: Entire video file read into RAM before writing to disk
- **File:** `backend/main.py:97-99`
- **Issue:** `content = await file.read()` reads the full file into memory, then writes it. A 500MB upload means 500MB+ heap spike.
- **Trigger:** Any large video upload.
- **Impact:** OOM kill on a 2GB RAM VPS (the minimum Hostinger KVM plan). Kills all three containers.
- **Suggested Fix:** Stream-write in 1MB chunks via walrus operator loop.
- **Status:** Fixed 2026-07-06

### BUG-005: pgvector index exists but is never used — all chunks loaded into RAM for similarity search
- **File:** `backend/main.py:159-171`
- **Issue:** `db.query(TranscriptChunk).filter(...).all()` loads every chunk for the video into Python, then `find_similar_chunks` computes cosine similarity in numpy. The pgvector ivfflat index in the DB is completely bypassed.
- **Trigger:** Any `/chats/{video_id}/ask` request on a video with many chunks (long video).
- **Impact:** For a 2-hour lecture (~500+ chunks), this loads ~500 × 384-float vectors into RAM on every question. Defeats the entire purpose of pgvector.
- **Suggested Fix:** Use `TranscriptChunk.embedding.cosine_distance(question_embedding)` directly in the DB query.
- **Status:** Fixed 2026-07-06

### BUG-006: Polling interval never cleared on component unmount
- **File:** `frontend/src/App.tsx:22-33`
- **Issue:** `setInterval` is created inside `handleVideoLoaded` but never stored in a ref or returned for cleanup. If the component unmounts while transcription is pending, the interval keeps firing and calls `setCurrentVideo` on a dead component.
- **Trigger:** User navigates away or the component unmounts before transcription finishes.
- **Impact:** Memory leak; React warning; ghost API calls forever.
- **Suggested Fix:** Store interval in `useRef`, clear in `useEffect` cleanup.
- **Status:** Fixed 2026-07-06

### BUG-007: `video` can be `None` in background task error handler
- **File:** `backend/main.py:66-69`
- **Issue:** In the `except` block, `video = db.query(Video).filter(...).first()` can return `None` if the record was deleted. `video.transcription_status = "failed"` then raises `AttributeError` silently.
- **Trigger:** Video record deleted while transcription is in progress.
- **Impact:** Exception in the except block — status never set to `failed`, error is lost.
- **Suggested Fix:** Add `if video:` guard before setting status.
- **Status:** Fixed 2026-07-06

### BUG-008: Division by zero in cosine similarity when a vector is all-zeros
- **File:** `backend/embeddings.py:80`
- **Issue:** `np.dot(q_vec, chunk_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(chunk_vec))` — if either norm is 0, numpy returns `nan`. `nan` comparisons in `sort` produce undefined ordering.
- **Trigger:** A zero-vector embedding (can happen for empty/whitespace-only chunk text).
- **Impact:** Silent wrong results — top-k chunks returned in arbitrary order.
- **Suggested Fix:** Guard denominator: `similarity = ... / denom if denom > 0 else 0.0`.
- **Status:** Fixed 2026-07-06

---

## 🟢 Normal

### BUG-009: `file.filename` used directly for path construction without sanitization
- **File:** `backend/main.py:94-95`
- **Issue:** `Path(file.filename).suffix` — `file.filename` is client-controlled. A filename like `../../etc/cron.d/evil.sh` or `NUL` (Windows) could produce unexpected paths. `.suffix` only extracts the extension so impact is limited, but the full filename should never be trusted.
- **Trigger:** Malicious or malformed filename in the multipart upload.
- **Impact:** Low here since only the suffix is used, but worth fixing for hygiene.
- **Suggested Fix:** Validate the suffix against an allowlist: `if file_extension not in {".mp4", ".mkv", ".mov", ".avi", ".webm"}: raise HTTPException(400, "Unsupported file type")`.
- **Status:** Open

### BUG-010: Uploaded file never deleted on transcription failure
- **File:** `backend/main.py:65-70`
- **Issue:** When transcription fails, the video file in `uploads/` is left on disk. The DB record is marked `failed` but the file stays forever.
- **Trigger:** Any transcription failure (bad audio, CUDA crash, etc.).
- **Impact:** Disk fills up silently over time, especially on a VPS with limited storage.
- **Suggested Fix:** In the `except` block, add `os.remove(file_path)` after marking status `failed` (with its own try/except to avoid masking the original error).
- **Status:** Open

### BUG-011: `chunk_transcript` infinite loop if `overlap >= chunk_size`
- **File:** `backend/embeddings.py:35`
- **Issue:** `i += int((chunk_size - overlap) / 1.3)` — if `overlap >= chunk_size`, the step is 0 or negative and the while loop never terminates.
- **Trigger:** Not currently triggered — call site uses `chunk_size=500, overlap=50`. Would trigger if someone changes the call or calls this function directly with bad args.
- **Not yet triggered** — hardcoded call values are safe.
- **Suggested Fix:** Add a guard at the top: `if overlap >= chunk_size: raise ValueError("overlap must be less than chunk_size")`.
- **Status:** Open

---

## ✅ Resolved

### BUG-001: openai proxies TypeError — Fixed 2026-07-06
Changed `openai==1.6.1` → `openai>=1.52.0` in requirements.txt. Also added `requests>=2.28.0` for faster-whisper utils.

### BUG-002: CUDA hardcoded in transcription.py — Fixed 2026-07-06
Auto-detect via `ctranslate2.get_cuda_device_count()`, falls back to `device="cpu", compute_type="int8"`.

### BUG-003: CORS wildcard + credentials — Fixed 2026-07-06
Set `allow_credentials=False` in CORS middleware.

### BUG-004: Full file read into RAM on upload — Fixed 2026-07-06
Replaced `file.read()` with 1MB chunked streaming write loop.

### BUG-005: pgvector index bypassed — Fixed 2026-07-06
Replaced Python numpy similarity with `TranscriptChunk.embedding.cosine_distance()` DB query.

### BUG-006: Polling interval leak on unmount — Fixed 2026-07-06
Stored interval in `pollIntervalRef`, clears on unmount via `useEffect` cleanup and on new video load.

### BUG-007: Null dereference in background task except block — Fixed 2026-07-06
Added `if video:` guard before setting `transcription_status = "failed"`.

### BUG-008: Division by zero in cosine similarity — Fixed 2026-07-06
Guard: `similarity = ... / denom if denom > 0 else 0.0`.
