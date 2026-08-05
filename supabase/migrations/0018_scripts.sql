-- Migration: 0018_scripts.sql
CREATE TABLE IF NOT EXISTS generated_scripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  topic TEXT NOT NULL,
  script_text TEXT NOT NULL,
  score FLOAT,
  cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
  attempts INT NOT NULL DEFAULT 1,
  scenes JSONB,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scripts_assistant ON generated_scripts(assistant_id, created_at DESC);

ALTER TABLE generated_scripts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_can_read_own_scripts" ON generated_scripts FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_scripts.assistant_id
        AND ca.user_id = auth.uid()
    )
  );
