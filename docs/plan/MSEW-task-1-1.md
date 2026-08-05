# Quy trình thực thi chi tiết (MSEW): Task 1.1

Sử dụng tool `run_command` (powershell) để tạo toàn bộ cấu trúc này trong một lệnh, hoặc dùng `write_to_file` tạo từng file. 

## BƯỚC 1: Tạo cấu trúc thư mục
Chạy lệnh tạo thư mục:
```bash
mkdir -p apps/api apps/worker packages/shared-types scripts supabase/migrations
```
*(Nếu dùng Windows PowerShell: `New-Item -ItemType Directory -Force -Path apps\api, apps\worker, packages\shared-types, scripts, supabase\migrations`)*

## BƯỚC 2: Tạo script sync_types
Tạo file `scripts/sync_types.py`:
```python
# Placeholder cho script sinh Zod schemas từ Pydantic
print("Syncing types... (To be implemented)")
```

## BƯỚC 3: Tạo 11 file SQL Migrations trong `supabase/migrations/`

**Tạo file `0001_users.sql`:**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  credits INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Tạo file `0002_jobs.sql`:**
```sql
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
```

**Tạo file `0003_credit_transactions.sql`:**
```sql
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  job_id UUID REFERENCES jobs(id),
  action TEXT NOT NULL,
  amount INT NOT NULL,
  balance_after INT NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_credit_tx_user ON credit_transactions(user_id, created_at DESC);
```

**Tạo file `0004_api_usage_logs.sql`:**
```sql
CREATE TABLE api_usage_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  job_id UUID REFERENCES jobs(id),
  provider TEXT NOT NULL,
  operation TEXT NOT NULL,
  input_tokens INT,
  output_tokens INT,
  cost_usd NUMERIC(10,6),
  quota_units INT,
  api_key_id TEXT,
  status_code INT,
  duration_ms INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_api_usage_provider_date ON api_usage_logs(provider, created_at DESC);
```

**Tạo file `0005_quota_ledger.sql`:**
```sql
CREATE TABLE quota_ledger (
  id BIGSERIAL PRIMARY KEY,
  api_key_id TEXT NOT NULL,
  date DATE NOT NULL,
  units_used INT NOT NULL DEFAULT 0,
  units_limit INT NOT NULL DEFAULT 10000,
  UNIQUE(api_key_id, date)
);
```

**Tạo file `0006_credit_hold_commit.sql`:**
```sql
-- Dựa trên E1 PRD v5
CREATE OR REPLACE FUNCTION partial_commit_credits(
    p_user_id UUID, p_job_id UUID, p_actual_cost INT
) RETURNS void AS $$
DECLARE v_held INT; v_refund INT;
BEGIN
    SELECT credits_held INTO v_held FROM jobs WHERE id = p_job_id FOR UPDATE;
    IF v_held IS NULL THEN RAISE EXCEPTION 'Job not found: %', p_job_id; END IF;
    IF p_actual_cost > v_held THEN RAISE EXCEPTION 'actual_cost > held'; END IF;
    v_refund := v_held - p_actual_cost;
    IF v_refund > 0 THEN
        UPDATE users SET credits = credits + v_refund, updated_at = NOW() WHERE id = p_user_id;
        INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
        VALUES (p_user_id, p_job_id, 'partial_refund', v_refund, (SELECT credits FROM users WHERE id = p_user_id), 'Partial refund');
    END IF;
    INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
    VALUES (p_user_id, p_job_id, 'commit', -p_actual_cost, (SELECT credits FROM users WHERE id = p_user_id), 'Committed');
    UPDATE jobs SET credits_held = 0 WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

**Tạo file `0007_rls_policies.sql`:**
```sql
-- Placeholder cho RLS ở Sprint 4
-- ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
```

**Tạo file `0008_channel_assistants.sql`:**
```sql
CREATE TABLE channel_assistants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  channel_id TEXT NOT NULL,
  name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Tạo file `0009_channel_deep_analysis.sql`:**
```sql
CREATE TABLE channel_deep_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assistant_id UUID NOT NULL REFERENCES channel_assistants(id) ON DELETE CASCADE,
  version INT NOT NULL DEFAULT 1,
  is_latest BOOLEAN NOT NULL DEFAULT TRUE,
  previous_version_id UUID REFERENCES channel_deep_analysis(id),
  reanalysis_trigger TEXT,
  metadata_report JSONB,
  tags_report JSONB,
  performance_report JSONB,
  hidden_insights JSONB,
  persona JSONB,
  hook_analysis JSONB,
  structural_formula JSONB,
  signature_phrases JSONB,
  mimic_rules JSONB,
  viral_topics_formula JSONB,
  untapped_opportunities JSONB,
  content_calendar JSONB,
  thumbnail_analysis JSONB,
  analysis_version TEXT DEFAULT 'v3.0',
  source_video_ids TEXT[],
  source_transcript_count INT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_deep_analysis_asst_latest ON channel_deep_analysis(assistant_id) WHERE is_latest = TRUE;
```

**Tạo file `0010_dna_chunks.sql`:**
```sql
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
```

**Tạo file `0011_transcripts_cron.sql`:**
```sql
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE TABLE transcripts (
  video_id TEXT PRIMARY KEY,
  text_content TEXT NOT NULL,
  raw_data JSONB,
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ GENERATED ALWAYS AS (fetched_at + INTERVAL '90 days') STORED
);
CREATE INDEX idx_transcripts_expires ON transcripts(expires_at);

-- Lên lịch dọn rác lúc 3AM mỗi ngày
SELECT cron.schedule('transcript-cleanup', '0 3 * * *', $$DELETE FROM transcripts WHERE expires_at < NOW()$$);
SELECT cron.schedule('cleanup-expired-dna-chunks', '0 4 * * *', $$DELETE FROM dna_chunks WHERE expires_at < NOW()$$);
```
