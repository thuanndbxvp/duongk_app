-- ============================================================
-- Migration: 0022_admin_panel_foundation.sql
-- Purpose: Cleanup + admin RBAC foundation
-- ============================================================

-- 1) Cleanup: xóa signature cũ của hold_credits (từ 0006) để tránh ambiguity
DROP FUNCTION IF EXISTS hold_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS partial_commit_credits(UUID, UUID, INT);
DROP FUNCTION IF EXISTS release_credits(UUID, UUID);

-- 2) Fix RLS transcripts: scope theo assistant_id thay vì 'all authenticated'
-- Xóa policy cũ "Authenticated users can view transcripts"
DROP POLICY IF EXISTS "Authenticated users can view transcripts" ON transcripts;

-- Policy mới: cho phép user đọc transcripts thuộc các assistant của mình
-- (qua JOIN bảng dna_chunks → assistant_id)
CREATE POLICY "Users can view own assistant transcripts" ON transcripts FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM dna_chunks dc
      JOIN channel_assistants ca ON ca.id = dc.assistant_id
      WHERE dc.source_video_id = transcripts.video_id
        AND ca.user_id = auth.uid()
    )
  );

-- Service role vẫn đọc được (cho worker ghi transcripts)
CREATE POLICY "Service can insert transcripts" ON transcripts FOR INSERT
  WITH CHECK (true);

-- 3) ALTER TABLE users: thêm columns cho admin RBAC + soft delete + ban
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'
    CHECK (role IN ('user', 'admin', 'super_admin')),
  ADD COLUMN IF NOT EXISTS max_assistants INT NOT NULL DEFAULT 5,
  ADD COLUMN IF NOT EXISTS banned_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS banned_reason TEXT,
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_sign_in_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS full_name TEXT;

-- Backfill từ auth metadata cho existing users
UPDATE users u
SET full_name = COALESCE(
  u.full_name,
  (SELECT au.raw_user_meta_data->>'full_name'
   FROM auth.users au
   WHERE au.id = u.id)
)
WHERE full_name IS NULL;

-- Partial index: chỉ index user chưa xoá
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier) WHERE deleted_at IS NULL;

-- 4) Bảng admin_audit_logs
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

-- RLS: deny non-service, chỉ service_role mới đọc/ghi
ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;
-- (không tạo policy → mặc định deny cho non-service)

-- 5) RPC admin_adjust_credits (atomic + audit-ready)
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

-- 6) RPC soft_delete_user
CREATE OR REPLACE FUNCTION soft_delete_user(p_user_id UUID) RETURNS void AS $$
BEGIN
  UPDATE users SET deleted_at = NOW() WHERE id = p_user_id AND deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;