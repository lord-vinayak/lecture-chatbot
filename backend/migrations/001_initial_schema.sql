-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Videos table
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  instructor_id UUID NOT NULL,
  transcript_text TEXT,
  transcription_status VARCHAR(50) DEFAULT 'pending' CHECK (transcription_status IN ('pending', 'completed', 'failed')),
  upload_date TIMESTAMP DEFAULT now(),
  file_path TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

-- Transcript chunks with embeddings
CREATE TABLE transcript_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  embedding vector(384),
  chunk_index INT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

-- Chat history
CREATE TABLE chats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  question TEXT NOT NULL,
  answer TEXT,
  source_chunks JSONB,
  created_at TIMESTAMP DEFAULT now()
);

-- Create indexes for fast search
CREATE INDEX idx_transcript_chunks_video_id ON transcript_chunks(video_id);
CREATE INDEX idx_transcript_chunks_embedding ON transcript_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_chats_video_id ON chats(video_id);
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_videos_status ON videos(transcription_status);
