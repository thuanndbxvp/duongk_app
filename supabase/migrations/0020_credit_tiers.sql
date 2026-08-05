-- ============================================================
-- Migration: 0020_credit_tiers.sql
-- Purpose: Credit tiers + helper functions
-- ============================================================

-- Update users table to add tier-specific defaults
ALTER TABLE users 
  ALTER COLUMN credits SET DEFAULT 100,
  ALTER COLUMN tier SET DEFAULT 'free';

-- Credit pricing table
CREATE TABLE IF NOT EXISTS credit_pricing (
  job_type TEXT PRIMARY KEY,
  credits INT NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO credit_pricing (job_type, credits, description) VALUES
  ('niche_validate', 5, 'Validate a YouTube niche'),
  ('collect_channel', 10, 'Collect metadata + transcripts'),
  ('deep_analysis', 50, 'Run 14-output deep analysis'),
  ('script_generation', 30, 'Generate AI script with RAG'),
  ('scene_breakdown', 10, 'Break script into scenes with B-roll'),
  ('idea_generation', 5, 'Generate HDBSCAN-based ideas'),
  ('rag_retrieve', 1, 'RAG context retrieval')
ON CONFLICT (job_type) DO NOTHING;

-- Hold credits function (atomic)
CREATE OR REPLACE FUNCTION hold_credits(
  p_user_id UUID,
  p_amount INT,
  p_job_id UUID
) RETURNS TABLE(
  transaction_id UUID,
  balance_after INT
) AS $$
DECLARE
  v_current_balance INT;
  v_tx_id UUID;
BEGIN
  -- Lock user row
  SELECT credits INTO v_current_balance
  FROM users WHERE id = p_user_id FOR UPDATE;
  
  IF v_current_balance IS NULL THEN
    RAISE EXCEPTION 'User not found';
  END IF;
  
  IF v_current_balance < p_amount THEN
    RAISE EXCEPTION 'Insufficient credits: have %, need %', v_current_balance, p_amount;
  END IF;
  
  -- Deduct
  UPDATE users SET credits = credits - p_amount WHERE id = p_user_id;
  
  -- Record transaction
  INSERT INTO credit_transactions (user_id, amount, job_id, job_type, metadata)
  VALUES (p_user_id, -p_amount, p_job_id, 'hold', jsonb_build_object('status', 'pending'))
  RETURNING id INTO v_tx_id;
  
  RETURN QUERY SELECT v_tx_id, v_current_balance - p_amount;
END;
$$ LANGUAGE plpgsql;

-- Refund credits (on failure)
CREATE OR REPLACE FUNCTION refund_credits(
  p_job_id UUID
) RETURNS INT AS $$
DECLARE
  v_tx RECORD;
  v_refund INT;
BEGIN
  SELECT * INTO v_tx FROM credit_transactions
  WHERE job_id = p_job_id AND metadata->>'status' = 'pending'
  LIMIT 1;
  
  IF v_tx IS NULL THEN
    RETURN 0;
  END IF;
  
  v_refund := ABS(v_tx.amount);
  
  -- Refund
  UPDATE users SET credits = credits + v_refund WHERE id = v_tx.user_id;
  
  -- Mark transaction as refunded
  UPDATE credit_transactions
  SET metadata = jsonb_set(metadata, '{status}', '"refunded"')
  WHERE id = v_tx.id;
  
  RETURN v_refund;
END;
$$ LANGUAGE plpgsql;
