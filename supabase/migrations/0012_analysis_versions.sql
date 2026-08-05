-- 0012_analysis_versions.sql
ALTER TABLE channel_deep_analysis
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS parent_version INT,
ADD COLUMN IF NOT EXISTS version_note TEXT;

CREATE INDEX IF NOT EXISTS idx_channel_deep_analysis_version ON channel_deep_analysis(version);
