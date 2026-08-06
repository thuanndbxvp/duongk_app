-- ============================================================
-- Migration: 0023_api_provider_keys.sql
-- Purpose: API provider key storage (encrypted via app-layer Fernet)
-- ============================================================

CREATE TABLE IF NOT EXISTS api_provider_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL,                   -- 'openai', 'gemini', 'cohere', 'elevenlabs', 'youtube', 'pexels', 'pixabay', 'unsplash', 'modal', 'supabase_service_role', 'r2', 'supadata', 'serpapi', 'groq'
  label TEXT NOT NULL,                      -- 'OpenAI key #1'
  encrypted_value BYTEA NOT NULL,           -- Fernet-encrypted raw value
  is_active BOOLEAN NOT NULL DEFAULT true,
  rate_limit_rpm INT,
  monthly_budget_usd NUMERIC(10,2),
  current_month_cost_usd NUMERIC(10,4) NOT NULL DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  last_tested_at TIMESTAMPTZ,
  last_test_status TEXT,                    -- 'ok' | 'fail' | 'timeout'
  last_test_latency_ms INT,
  last_test_error TEXT,
  expires_at TIMESTAMPTZ,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  archived_at TIMESTAMPTZ,                  -- Soft archive (giữ value 7 ngày)
  UNIQUE(provider, label)
);

CREATE INDEX IF NOT EXISTS idx_apikeys_provider_active ON api_provider_keys(provider) WHERE is_active AND archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_apikeys_archived ON api_provider_keys(archived_at) WHERE archived_at IS NOT NULL;

-- RLS: deny non-service, only service_role reads/writes
ALTER TABLE api_provider_keys ENABLE ROW LEVEL SECURITY;
-- (không tạo policy → default deny)