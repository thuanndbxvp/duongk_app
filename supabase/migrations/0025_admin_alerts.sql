-- ============================================================
-- Migration: 0025_admin_alerts.sql
-- Purpose: Admin alerts (budget/quota/error rate)
-- ============================================================

CREATE TABLE IF NOT EXISTS admin_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  severity TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
  category TEXT NOT NULL,                -- 'budget', 'quota', 'error_rate', 'security'
  message TEXT NOT NULL,
  context JSONB DEFAULT '{}',
  resolved_at TIMESTAMPTZ,
  resolved_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON admin_alerts(created_at DESC) WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON admin_alerts(severity, created_at DESC);

ALTER TABLE admin_alerts ENABLE ROW LEVEL SECURITY;

-- RPC: create_alert (idempotent per category + context hash)
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
  
  -- Idempotent: nếu đã có unresolved alert với cùng category + context_hash → không insert mới
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