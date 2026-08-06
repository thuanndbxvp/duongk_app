-- One-shot fix: add `metadata` column to credit_transactions so RPC
-- admin_adjust_credits (which inserts into metadata) works.
--
-- Run this in Supabase SQL Editor:
--   https://app.supabase.com/project/<your-project>/sql/new
--
-- OR via psql:
--   psql "<SUPABASE_DB_URL>" -f supabase/fix-0029-credit-tx-metadata.sql

ALTER TABLE credit_transactions
  ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT NULL;

COMMENT ON COLUMN credit_transactions.metadata IS
  'Optional structured payload (e.g. {"admin_id": "..."} for admin adjustment).';
