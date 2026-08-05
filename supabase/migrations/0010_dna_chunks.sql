CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE dna_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  source_video_id TEXT NOT NULL,
  section TEXT NOT NULL,
  chunk_index INT NOT NULL,
  text_content TEXT NOT NULL,
  word_count INT,
  timestamp_start_sec NUMERIC,
  timestamp_end_sec NUMERIC,
  embedding VECTOR(1024), -- E3: Force 1024d for Cohere + OpenAI
  embedding_model TEXT NOT NULL DEFAULT 'cohere:embed-multilingual-v3.0',
  expires_at TIMESTAMPTZ GENERATED ALWAYS AS (NOW() + INTERVAL '90 days') STORED,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_dna_chunks_asst ON dna_chunks(assistant_id);