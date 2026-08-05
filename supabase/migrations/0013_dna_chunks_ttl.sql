-- E6 FIX: Add TTL columns to dna_chunks
ALTER TABLE dna_chunks 
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '90 days'),
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_dna_chunks_expires ON dna_chunks(expires_at) WHERE is_active = true;

SELECT cron.schedule('cleanup-expired-dna-chunks', '0 4 * * *',
    $$DELETE FROM dna_chunks WHERE expires_at < NOW() AND is_active = true$$);
