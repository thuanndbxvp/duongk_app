-- 0014_progress_sub.rpc.sql
-- RPC for updating job sub_progress safely
CREATE OR REPLACE FUNCTION update_job_sub_progress(
    p_job_id UUID,
    p_output_key TEXT,
    p_progress_value JSONB,
    p_is_complete BOOLEAN DEFAULT false
) RETURNS void AS $$
DECLARE
    v_current_progress JSONB;
BEGIN
    -- Use FOR UPDATE to prevent race conditions when multiple workers update progress
    SELECT sub_progress INTO v_current_progress 
    FROM jobs 
    WHERE id = p_job_id 
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job % not found', p_job_id;
    END IF;

    -- Update the specific output key in the JSONB
    UPDATE jobs 
    SET 
        sub_progress = jsonb_set(COALESCE(sub_progress, '{}'::jsonb), array[p_output_key], p_progress_value, true),
        updated_at = NOW()
    WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql VOLATILE;
