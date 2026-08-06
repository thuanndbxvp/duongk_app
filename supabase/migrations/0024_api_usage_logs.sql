-- ============================================================
-- Migration: 0024_api_usage_logs.sql
-- Purpose: Track API usage + cost per provider key
-- ============================================================

CREATE TABLE IF NOT EXISTS api_usage_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider_key_id UUID NOT NULL REFERENCES api_provider_keys(id) ON DELETE CASCADE,
  feature TEXT,                              -- 'llm_text', 'embedding', 'tts', ...
  success BOOLEAN NOT NULL,
  latency_ms INT,
  cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
  error_code TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_key_time ON api_usage_logs(provider_key_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_feature_time ON api_usage_logs(feature, created_at DESC);

-- RLS: deny non-service
ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;

-- Drop view first (nếu đã tồn tại từ migration cũ bị fail)
DROP VIEW IF EXISTS api_usage_summary CASCADE;

-- View: aggregated cost per provider (24h/7d/30d)
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