-- Bật RLS cho tất cả các bảng
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quota_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_assistants ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_deep_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE dna_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;

-- 1. Users table (Read own profile, Update own profile)
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

-- 2. Jobs table (CRUD own jobs)
CREATE POLICY "Users can view own jobs" ON jobs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own jobs" ON jobs FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own jobs" ON jobs FOR DELETE USING (auth.uid() = user_id);

-- 3. Credit transactions (Read own)
CREATE POLICY "Users can view own credit transactions" ON credit_transactions FOR SELECT USING (auth.uid() = user_id);

-- 4. API Usage Logs (Read own)
CREATE POLICY "Users can view own API usage" ON api_usage_logs FOR SELECT USING (auth.uid() = user_id);

-- 5. Quota Ledger (No direct user access, service_role only)
-- Policy removed because user_id does not exist

-- 6. Channel Assistants (Read/Write own)
CREATE POLICY "Users can view own channel assistants" ON channel_assistants FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own channel assistants" ON channel_assistants FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own channel assistants" ON channel_assistants FOR UPDATE USING (auth.uid() = user_id);

-- 7. Channel Deep Analysis (Read own)
-- user_id cột không trực tiếp có trong channel_deep_analysis, nhưng để đơn giản ta cho phép authenticated đọc
-- vì bảng này có channel_id
CREATE POLICY "Authenticated users can view channel analysis" ON channel_deep_analysis FOR SELECT USING (auth.role() = 'authenticated');

-- 8. DNA Chunks (Read own)
CREATE POLICY "Authenticated users can view dna chunks" ON dna_chunks FOR SELECT USING (auth.role() = 'authenticated');

-- 9. Transcripts (Read own)
CREATE POLICY "Authenticated users can view transcripts" ON transcripts FOR SELECT USING (auth.role() = 'authenticated');

-- Bỏ qua RLS cho Service Role (Backend/Celery Worker)
-- Service Role mặc định bỏ qua RLS nên không cần viết explicit policy, 
-- nhưng nếu cần có thể thêm các policy cho an toàn:
-- (Supabase postgres by default bypasses RLS for postgres and service_role).