CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  task_type TEXT NOT NULL,
  celery_task_id TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending',
  progress INT DEFAULT 0,
  sub_progress JSONB DEFAULT '{}'::jsonb,
  input_payload JSONB,
  result_payload JSONB,
  error_message TEXT,
  credits_held INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);