-- ============================================================
-- SETUP-PHASE5-CHUNKED.SQL
-- Run từng query một trong Supabase Dashboard SQL Editor.
-- Mỗi query là idempotent + an toàn khi re-run.
-- ============================================================

-- ============================================================
-- Q1: Drop dangling signatures từ migration 0006 (nếu có)
-- ============================================================
DROP FUNCTION IF EXISTS hold_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS partial_commit_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS release_credits(UUID, UUID);

-- ============================================================
-- Q2: Drop & re-create transcripts RLS policy (nếu có)
-- ============================================================
DROP POLICY IF EXISTS "Authenticated users can view transcripts" ON transcripts;
DROP POLICY IF EXISTS "Users can view own assistant transcripts" ON transcripts;

CREATE POLICY "Users can view own assistant transcripts" ON transcripts FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM dna_chunks dc
      JOIN channel_assistants ca ON ca.id = dc.assistant_id
      WHERE dc.source_video_id = transcripts.video_id
        AND ca.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Service can insert transcripts" ON transcripts;
CREATE POLICY "Service can insert transcripts" ON transcripts FOR INSERT
  WITH CHECK (true);

-- ============================================================
-- Q3: ALTER TABLE users — thêm columns RBAC
-- ============================================================
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'
    CHECK (role IN ('user', 'admin', 'super_admin')),
  ADD COLUMN IF NOT EXISTS max_assistants INT NOT NULL DEFAULT 5,
  ADD COLUMN IF NOT EXISTS banned_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS banned_reason TEXT,
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_sign_in_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS full_name TEXT;

-- Q3b: Backfill full_name từ auth metadata cho existing users (idempotent)
UPDATE users u
SET full_name = COALESCE(
  u.full_name,
  (SELECT au.raw_user_meta_data->>'full_name'
   FROM auth.users au
   WHERE au.id = u.id)
)
WHERE full_name IS NULL;

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier) WHERE deleted_at IS NULL;

-- ============================================================
-- Q4: CREATE TABLE admin_audit_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id UUID NOT NULL REFERENCES users(id),
  admin_email TEXT NOT NULL,
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  before JSONB,
  after JSONB,
  ip INET,
  user_agent TEXT,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_admin ON admin_audit_logs(admin_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_target ON admin_audit_logs(target_type, target_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON admin_audit_logs(action, created_at DESC);

ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Q5: CREATE TABLE api_provider_keys
-- ============================================================
CREATE TABLE IF NOT EXISTS api_provider_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL,
  label TEXT NOT NULL,
  encrypted_value BYTEA NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  rate_limit_rpm INT,
  monthly_budget_usd NUMERIC(10,2),
  current_month_cost_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  last_tested_at TIMESTAMPTZ,
  last_test_status TEXT,
  last_test_latency_ms INT,
  last_test_error TEXT,
  expires_at TIMESTAMPTZ,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  archived_at TIMESTAMPTZ,
  UNIQUE(provider, label)
);

CREATE INDEX IF NOT EXISTS idx_apikeys_provider_active ON api_provider_keys(provider) WHERE is_active AND archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_apikeys_archived ON api_provider_keys(archived_at) WHERE archived_at IS NOT NULL;

ALTER TABLE api_provider_keys ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Q6: DROP VIEW + CREATE TABLE api_usage_logs
-- (DROP VIEW first để tránh column provider_key_id does not exist)
-- ============================================================
DROP VIEW IF EXISTS api_usage_summary CASCADE;

CREATE TABLE IF NOT EXISTS api_usage_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_key_id UUID NOT NULL REFERENCES api_provider_keys(id) ON DELETE CASCADE,
  feature TEXT,
  success BOOLEAN NOT NULL,
  latency_ms INT,
  cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
  error_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_key_time ON api_usage_logs(provider_key_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_feature_time ON api_usage_logs(feature, created_at DESC);

ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Q7: CREATE VIEW api_usage_summary (SAU Q6 — table đã tồn tại)
-- ============================================================
DROP VIEW IF EXISTS api_usage_summary CASCADE;

CREATE OR REPLACE VIEW api_usage_summary AS
SELECT
  provider_key_id,
  feature,
  COUNT(*) AS total_calls,
  COUNT(*) FILTER (WHERE success) AS success_calls,
  ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms,
  SUM(cost_usd) AS total_cost_usd,
  DATE_TRUNC('hour', created_at) AS hour_bucket
FROM api_usage_logs
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY provider_key_id, feature, DATE_TRUNC('hour', created_at);

-- ============================================================
-- Q8: CREATE TABLE admin_alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  severity TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
  category TEXT NOT NULL,
  message TEXT NOT NULL,
  context JSONB DEFAULT '{}',
  resolved_at TIMESTAMPTZ,
  resolved_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON admin_alerts(created_at DESC) WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON admin_alerts(severity, created_at DESC);

ALTER TABLE admin_alerts ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Q9: CREATE TABLE service_routing_config + seed (8 features)
-- ============================================================
CREATE TABLE IF NOT EXISTS service_routing_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  feature TEXT NOT NULL UNIQUE,
  primary_provider TEXT NOT NULL,
  fallback_chain TEXT[] NOT NULL DEFAULT '{}',
  enabled_providers JSONB NOT NULL DEFAULT '{}',
  cost_per_call_usd JSONB NOT NULL DEFAULT '{}',
  config_version INT NOT NULL DEFAULT 1,
  updated_by UUID REFERENCES users(id),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_routing_feature ON service_routing_config(feature);

INSERT INTO service_routing_config (feature, primary_provider, fallback_chain, enabled_providers, cost_per_call_usd) VALUES
  ('transcript_extract', 'supadata', ARRAY['groq','youtube_transcript_api','openai','modal_whisper']::TEXT[],
   '{"supadata":true,"groq":true,"youtube_transcript_api":true,"openai":true,"modal_whisper":true}'::jsonb,
   '{"supadata":0.001,"groq":0.00067,"youtube_transcript_api":0,"openai":0.006,"modal_whisper":0.006}'::jsonb),
  ('llm_text', 'openai', ARRAY['stali']::TEXT[],
   '{"openai":true,"stali":true}'::jsonb,
   '{"openai":0.005,"stali":0.002}'::jsonb),
  ('embedding', 'cohere', ARRAY['openai']::TEXT[],
   '{"cohere":true,"openai":true}'::jsonb,
   '{"cohere":0.0001,"openai":0.00013}'::jsonb),
  ('emotion_classifier', 'openai', ARRAY[]::TEXT[],
   '{"openai":true}'::jsonb,
   '{"openai":0.0005}'::jsonb),
  ('ffmpeg_render', 'modal_t4', ARRAY['modal_a10g','local_cpu']::TEXT[],
   '{"modal_t4":true,"modal_a10g":true,"local_cpu":true}'::jsonb,
   '{"modal_t4":0.02,"modal_a10g":0.04,"local_cpu":0.0}'::jsonb),
  ('tts', 'modal_omnivoice', ARRAY['elevenlabs','openai_tts']::TEXT[],
   '{"modal_omnivoice":true,"elevenlabs":true,"openai_tts":true}'::jsonb,
   '{"modal_omnivoice":0.008,"elevenlabs":0.018,"openai_tts":0.015}'::jsonb),
  ('thumbnail_vision', 'openai', ARRAY['gemini']::TEXT[],
   '{"openai":true,"gemini":false}'::jsonb,
   '{"openai":0.0075,"gemini":0.0025}'::jsonb),
  ('footage_search', 'pexels', ARRAY['pixabay','unsplash']::TEXT[],
   '{"pexels":true,"pixabay":true,"unsplash":true}'::jsonb,
   '{"pexels":0,"pixabay":0,"unsplash":0}'::jsonb)
ON CONFLICT (feature) DO UPDATE SET
  primary_provider = EXCLUDED.primary_provider,
  fallback_chain = EXCLUDED.fallback_chain,
  enabled_providers = EXCLUDED.enabled_providers,
  cost_per_call_usd = EXCLUDED.cost_per_call_usd,
  config_version = service_routing_config.config_version + 1,
  updated_at = NOW();

ALTER TABLE service_routing_config ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Q10: Trigger notify_routing_update
-- ============================================================
CREATE OR REPLACE FUNCTION notify_routing_update() RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('routing:config:update', NEW.feature);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_routing_update ON service_routing_config;
CREATE TRIGGER trigger_routing_update
  AFTER UPDATE ON service_routing_config
  FOR EACH ROW
  WHEN (OLD.* IS DISTINCT FROM NEW.*)
  EXECUTE FUNCTION notify_routing_update();

-- ============================================================
-- Q11: CREATE TABLE mfa_challenges + mfa_backup_codes
-- ============================================================
CREATE TABLE IF NOT EXISTS mfa_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending','active','disabled')),
  encrypted_secret BYTEA NOT NULL,
  qr_uri TEXT,
  enrolled_at TIMESTAMPTZ,
  last_verified_at TIMESTAMPTZ,
  failed_attempts INT NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, status) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS idx_mfa_user_status ON mfa_challenges(user_id, status);

CREATE TABLE IF NOT EXISTS mfa_backup_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backup_codes_user ON mfa_backup_codes(user_id);

ALTER TABLE mfa_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE mfa_backup_codes ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Q12: Indexes for credit_transactions (cho analytics RPCs)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_credit_tx_created ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_tx_action_created ON credit_transactions(action, created_at DESC);

-- ============================================================
-- Q13: RPCs (admin_adjust_credits, soft_delete_user, create_alert,
--                record_mfa_failure, revenue_by_day, cohort_retention,
--                top_creators)
-- ============================================================
CREATE OR REPLACE FUNCTION admin_adjust_credits(
  p_admin_id UUID,
  p_user_id UUID,
  p_delta INT,
  p_reason TEXT
) RETURNS TABLE(new_balance INT, tx_id UUID) AS $$
DECLARE
  v_current INT;
  v_tx_id UUID;
BEGIN
  IF p_reason IS NULL OR length(trim(p_reason)) < 10 THEN
    RAISE EXCEPTION 'Reason required (min 10 chars)';
  END IF;

  SELECT credits INTO v_current FROM users WHERE id = p_user_id FOR UPDATE;
  IF v_current IS NULL THEN RAISE EXCEPTION 'User not found'; END IF;

  UPDATE users SET credits = credits + p_delta, updated_at = NOW() WHERE id = p_user_id;

  INSERT INTO credit_transactions (user_id, action, amount, balance_after, reason, metadata)
  VALUES (p_user_id, 'admin_adjust', p_delta, v_current + p_delta, p_reason,
          jsonb_build_object('admin_id', p_admin_id))
  RETURNING id INTO v_tx_id;

  RETURN QUERY SELECT v_current + p_delta, v_tx_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION soft_delete_user(p_user_id UUID) RETURNS void AS $$
BEGIN
  UPDATE users SET deleted_at = NOW() WHERE id = p_user_id AND deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_alert(
  p_severity TEXT,
  p_category TEXT,
  p_message TEXT,
  p_context JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
  v_id UUID;
  v_context_hash TEXT;
BEGIN
  v_context_hash := md5(p_context::text);

  IF EXISTS (
    SELECT 1 FROM admin_alerts
    WHERE category = p_category
      AND resolved_at IS NULL
      AND md5(context::text) = v_context_hash
      AND created_at > NOW() - INTERVAL '1 hour'
  ) THEN
    SELECT id INTO v_id FROM admin_alerts
    WHERE category = p_category
      AND resolved_at IS NULL
      AND md5(context::text) = v_context_hash
    LIMIT 1;
    RETURN v_id;
  END IF;

  INSERT INTO admin_alerts (severity, category, message, context)
  VALUES (p_severity, p_category, p_message, p_context)
  RETURNING id INTO v_id;

  RETURN v_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION record_mfa_failure(p_user_id UUID) RETURNS VOID AS $$
BEGIN
  UPDATE mfa_challenges
  SET failed_attempts = failed_attempts + 1,
      locked_until = CASE WHEN failed_attempts + 1 >= 5 THEN NOW() + INTERVAL '15 minutes' ELSE locked_until END,
      updated_at = NOW()
  WHERE user_id = p_user_id AND status = 'active';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION revenue_by_day(p_days INT DEFAULT 30)
RETURNS TABLE(day DATE, total_credits_consumed BIGINT, total_users BIGINT) AS $$
BEGIN
  RETURN QUERY
  SELECT
    DATE_TRUNC('day', ct.created_at)::DATE AS day,
    SUM(ABS(ct.amount))::BIGINT AS total_credits_consumed,
    COUNT(DISTINCT ct.user_id)::BIGINT AS total_users
  FROM credit_transactions ct
  WHERE ct.action = 'consume'
    AND ct.created_at >= NOW() - (p_days || ' days')::INTERVAL
    AND p_days > 0
    AND p_days <= 90
  GROUP BY day
  ORDER BY day DESC;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION cohort_retention(p_cohort_weeks INT DEFAULT 8)
RETURNS TABLE(
  cohort_week DATE,
  week_offset INT,
  active_users BIGINT,
  cohort_size BIGINT,
  retention_pct NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  WITH cohorts AS (
    SELECT
      DATE_TRUNC('week', u.created_at)::DATE AS cohort_week,
      u.id AS user_id
    FROM users u
    WHERE u.created_at >= NOW() - (p_cohort_weeks || ' weeks')::INTERVAL
  ),
  cohort_sizes AS (
    SELECT cohort_week, COUNT(*) AS cohort_size
    FROM cohorts
    GROUP BY cohort_week
  )
  SELECT
    c.cohort_week,
    EXTRACT(WEEK FROM AGE(act.created_at, c.cohort_week))::INT AS week_offset,
    COUNT(DISTINCT act.user_id)::BIGINT AS active_users,
    cs.cohort_size::BIGINT,
    ROUND(COUNT(DISTINCT act.user_id)::NUMERIC / NULLIF(cs.cohort_size, 0), 4) AS retention_pct
  FROM cohorts c
  JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week
  LEFT JOIN credit_transactions act ON act.user_id = c.user_id
  GROUP BY c.cohort_week, week_offset, cs.cohort_size
  ORDER BY c.cohort_week DESC, week_offset ASC
  LIMIT p_cohort_weeks * p_cohort_weeks;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION top_creators(p_metric TEXT DEFAULT 'assistants', p_limit INT DEFAULT 10)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  metric_value BIGINT,
  tier TEXT,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  IF p_metric = 'assistants' THEN
    RETURN QUERY
    SELECT u.id, u.email, COUNT(ca.id)::BIGINT, u.tier, u.created_at
    FROM users u
    LEFT JOIN channel_assistants ca ON ca.user_id = u.id
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COUNT(ca.id) > 0
    ORDER BY COUNT(ca.id) DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSIF p_metric = 'credits_consumed' THEN
    RETURN QUERY
    SELECT u.id, u.email, COALESCE(SUM(ABS(ct.amount)), 0)::BIGINT, u.tier, u.created_at
    FROM users u
    LEFT JOIN credit_transactions ct ON ct.user_id = u.id AND ct.action = 'consume'
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COALESCE(SUM(ABS(ct.amount)), 0) > 0
    ORDER BY COALESCE(SUM(ABS(ct.amount)), 0) DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSE
    RETURN;
  END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================
-- Q14: VERIFY + UPGRADE SUPER_ADMIN
-- ============================================================

-- 14a) Verify columns
SELECT
  'users.role exists' AS check_name,
  EXISTS(
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'role'
  ) AS ok;

-- 14b) Verify tables
SELECT
  t.table_name,
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = t.table_name) AS exists
FROM (VALUES
  ('admin_audit_logs'),
  ('admin_alerts'),
  ('api_provider_keys'),
  ('api_usage_logs'),
  ('service_routing_config'),
  ('mfa_challenges'),
  ('mfa_backup_codes')
) AS t(table_name)
ORDER BY t.table_name;

-- 14c) Upgrade nobita6986@gmail.com to super_admin
UPDATE users
SET role = 'super_admin', updated_at = NOW()
WHERE email = 'nobita6986@gmail.com' AND deleted_at IS NULL
RETURNING id, email, role, tier, credits;
