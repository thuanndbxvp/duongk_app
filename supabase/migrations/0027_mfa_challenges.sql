-- ============================================================
-- Migration: 0027_mfa_challenges.sql
-- Purpose: MFA TOTP + backup codes storage for super_admin
-- ============================================================

-- Main MFA enrollment table
CREATE TABLE IF NOT EXISTS mfa_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('pending','active','disabled')),
  encrypted_secret BYTEA NOT NULL,           -- Fernet-encrypted TOTP secret
  qr_uri TEXT,                               -- otpauth:// URI
  enrolled_at TIMESTAMPTZ,
  last_verified_at TIMESTAMPTZ,
  failed_attempts INT NOT NULL DEFAULT 0,
  locked_until TIMESTAMPTZ,                  -- Brute force lockout (5 fail → 15 min)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, status) DEFERRABLE INITIALLY DEFERRED  -- 1 active per user
);

CREATE INDEX IF NOT EXISTS idx_mfa_user_status ON mfa_challenges(user_id, status);

-- Backup codes table (10 codes per user, 1-time use)
CREATE TABLE IF NOT EXISTS mfa_backup_codes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  code_hash TEXT NOT NULL,                   -- SHA-256 hex of code
  used_at TIMESTAMPTZ,                       -- null = unused
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backup_codes_user ON mfa_backup_codes(user_id);

-- RLS: deny non-service
ALTER TABLE mfa_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE mfa_backup_codes ENABLE ROW LEVEL SECURITY;

-- RPC: increment failed_attempts + lock if needed (atomic)
CREATE OR REPLACE FUNCTION record_mfa_failure(p_user_id UUID) RETURNS VOID AS $$
BEGIN
  UPDATE mfa_challenges
  SET failed_attempts = failed_attempts + 1,
      locked_until = CASE WHEN failed_attempts + 1 >= 5 THEN NOW() + INTERVAL '15 minutes' ELSE locked_until END,
      updated_at = NOW()
  WHERE user_id = p_user_id AND status = 'active';
END;
$$ LANGUAGE plpgsql;