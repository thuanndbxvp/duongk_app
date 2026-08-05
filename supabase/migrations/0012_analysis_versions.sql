-- E7 FIX: Versioning for channel_deep_analysis

ALTER TABLE channel_deep_analysis 
    ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS parent_version INTEGER,
    ADD COLUMN IF NOT EXISTS version_note TEXT;

CREATE OR REPLACE FUNCTION create_analysis_version()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM channel_deep_analysis WHERE channel_id = NEW.channel_id) THEN
        SELECT COALESCE(MAX(version), 0) INTO NEW.version FROM channel_deep_analysis WHERE channel_id = NEW.channel_id;
        NEW.version = COALESCE(NEW.version, 0) + 1;
        NEW.parent_version = NEW.version - 1;
    ELSE
        NEW.version = 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_analysis_version ON channel_deep_analysis;
CREATE TRIGGER trigger_analysis_version
    BEFORE INSERT ON channel_deep_analysis
    FOR EACH ROW
    EXECUTE FUNCTION create_analysis_version();
