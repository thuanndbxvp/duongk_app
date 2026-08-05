-- Dựa trên E1 PRD v5
CREATE OR REPLACE FUNCTION partial_commit_credits(
    p_user_id UUID, p_job_id UUID, p_actual_cost INT
) RETURNS void AS $$
DECLARE v_held INT; v_refund INT;
BEGIN
    SELECT credits_held INTO v_held FROM jobs WHERE id = p_job_id FOR UPDATE;
    IF v_held IS NULL THEN RAISE EXCEPTION 'Job not found: %', p_job_id; END IF;
    IF p_actual_cost > v_held THEN RAISE EXCEPTION 'actual_cost > held'; END IF;
    v_refund := v_held - p_actual_cost;
    IF v_refund > 0 THEN
        UPDATE users SET credits = credits + v_refund, updated_at = NOW() WHERE id = p_user_id;
        INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
        VALUES (p_user_id, p_job_id, 'partial_refund', v_refund, (SELECT credits FROM users WHERE id = p_user_id), 'Partial refund');
    END IF;
    INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
    VALUES (p_user_id, p_job_id, 'commit', -p_actual_cost, (SELECT credits FROM users WHERE id = p_user_id), 'Committed');
    UPDATE jobs SET credits_held = 0 WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql VOLATILE;