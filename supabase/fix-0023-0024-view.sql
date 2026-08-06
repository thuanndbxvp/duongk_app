-- ============================================================
-- FIX: Migration 0023 + 0024 — drop views first
-- ============================================================

-- 0023_api_provider_keys.sql (already exists, this is idempotent)
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

-- 0024_api_usage_logs.sql — DROP VIEW FIRST to avoid stale ref
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

-- View (re-create AFTER table)
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

-- Verify
SELECT 'api_provider_keys' AS t, COUNT(*) FROM api_provider_keys
UNION ALL
SELECT 'api_usage_logs', COUNT(*) FROM api_usage_logs;