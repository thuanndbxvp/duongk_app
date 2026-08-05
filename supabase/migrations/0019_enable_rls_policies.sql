-- ============================================================
-- Migration: 0019_enable_rls_policies.sql
-- Purpose: Enable RLS + policies for production users
-- ============================================================

-- 1. Users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_data" ON users;
CREATE POLICY "users_own_data" ON users FOR ALL
  USING (id = auth.uid());

-- 2. Jobs table
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_jobs" ON jobs;
CREATE POLICY "users_own_jobs" ON jobs FOR ALL
  USING (user_id = auth.uid());

-- 3. Credit transactions
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_credit_tx" ON credit_transactions;
CREATE POLICY "users_own_credit_tx" ON credit_transactions FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users u
      WHERE u.id = credit_transactions.user_id
        AND u.id = auth.uid()
    )
  );

-- 4. Channel assistants
ALTER TABLE channel_assistants ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_assistants" ON channel_assistants;
CREATE POLICY "users_own_assistants" ON channel_assistants FOR ALL
  USING (user_id = auth.uid());

-- 5. Channel deep analysis (via assistant)
ALTER TABLE channel_deep_analysis ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_analysis" ON channel_deep_analysis;
CREATE POLICY "users_own_analysis" ON channel_deep_analysis FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = channel_deep_analysis.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- 6. DNA chunks (via assistant)
ALTER TABLE dna_chunks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_chunks" ON dna_chunks;
CREATE POLICY "users_own_chunks" ON dna_chunks FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = dna_chunks.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- 7. Generated ideas (via assistant)
ALTER TABLE generated_ideas ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_ideas" ON generated_ideas;
CREATE POLICY "users_own_ideas" ON generated_ideas FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_ideas.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- 8. Generated scripts (via assistant)
ALTER TABLE generated_scripts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "users_own_scripts" ON generated_scripts;
CREATE POLICY "users_own_scripts" ON generated_scripts FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM channel_assistants ca
      WHERE ca.id = generated_scripts.assistant_id
        AND ca.user_id = auth.uid()
    )
  );

-- Note: service_role bypasses RLS by default (for Celery worker)
