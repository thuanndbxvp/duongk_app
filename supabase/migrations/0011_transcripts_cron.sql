CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE TABLE transcripts (
  video_id TEXT PRIMARY KEY,
  text_content TEXT NOT NULL,
  raw_data JSONB,
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days')
);
CREATE INDEX idx_transcripts_expires ON transcripts(expires_at);

-- Lên lịch dọn rác lúc 3AM mỗi ngày
SELECT cron.schedule('transcript-cleanup', '0 3 * * *', $$DELETE FROM transcripts WHERE expires_at < NOW()$$);
SELECT cron.schedule('cleanup-expired-dna-chunks', '0 4 * * *', $$DELETE FROM dna_chunks WHERE expires_at < NOW()$$);