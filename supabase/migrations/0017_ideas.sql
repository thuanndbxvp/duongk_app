-- ============================================================
-- Migration: 0017_ideas.sql
-- Purpose: Table for generated ideas/opportunities
-- ============================================================

CREATE TABLE IF NOT EXISTS generated_ideas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  idea_topic TEXT NOT NULL,
  gap_score FLOAT,
  cluster_id INT,
  related_videos JSONB,
  opportunity_description TEXT,
  confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ideas_assistant ON generated_ideas(assistant_id, gap_score DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_cluster ON generated_ideas(assistant_id, cluster_id);

-- RLS
ALTER TABLE generated_ideas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_ideas" ON generated_ideas FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_ideas.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

CREATE POLICY "service_can_insert_ideas" ON generated_ideas FOR INSERT
  WITH CHECK (true);  -- Worker uses service_role
