-- D1 FIX: Race-safe sub_progress update
CREATE OR REPLACE FUNCTION update_job_sub_progress(
    p_job_id UUID,
    p_output_key TEXT,
    p_progress_value JSONB,
    p_is_complete BOOLEAN DEFAULT false
)
RETURNS VOID AS $$
DECLARE
    v_current JSONB;
BEGIN
    -- Lock row to prevent concurrent updates
    SELECT sub_progress INTO v_current
    FROM jobs
    WHERE id = p_job_id
    FOR UPDATE;
    
    -- Get current or init
    v_current := COALESCE(v_current, '{}'::jsonb);
    
    -- Update specific key
    v_current := jsonb_set(v_current, ARRAY[p_output_key], p_progress_value);
    
    -- Update jobs table
    UPDATE jobs SET sub_progress = v_current, updated_at = NOW() WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION update_job_sub_progress TO authenticated;
