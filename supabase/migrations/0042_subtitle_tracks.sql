-- Migration: subtitle_tracks table
-- Tier 1 P0 — Subtitle generation without Celery

CREATE TABLE IF NOT EXISTS subtitle_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    format TEXT NOT NULL DEFAULT 'srt',
    storage_key TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookup by project
CREATE INDEX IF NOT EXISTS idx_subtitle_tracks_project_id ON subtitle_tracks(project_id);
CREATE INDEX IF NOT EXISTS idx_subtitle_tracks_status ON subtitle_tracks(status);

-- RLS Policies
ALTER TABLE subtitle_tracks ENABLE ROW LEVEL SECURITY;

-- Users can read their own subtitle tracks
CREATE POLICY "Users can read own subtitle tracks"
    ON subtitle_tracks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = subtitle_tracks.project_id
            AND projects.user_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage subtitle tracks"
    ON subtitle_tracks FOR ALL
    USING (auth.role() = 'service_role');

COMMENT ON TABLE subtitle_tracks IS 'Stores generated subtitle tracks (SRT, VTT)';
