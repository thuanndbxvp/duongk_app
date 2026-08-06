-- Fix: admin_adjust_credits RPC references `metadata` column that doesn't exist
-- on credit_transactions. Add the column (jsonb, nullable) so the RPC works.
--
-- See admin_users.py adjust_credit() → db.rpc('admin_adjust_credits', ...)
-- The RPC body does:
--   INSERT INTO credit_transactions (..., metadata) VALUES (..., jsonb_build_object('admin_id', ...))

ALTER TABLE credit_transactions
  ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT NULL;

COMMENT ON COLUMN credit_transactions.metadata IS
  'Optional structured payload (e.g. {"admin_id": "..."} for admin adjustment).';
