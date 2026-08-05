-- Dựa trên E1 PRD v5
-- Hold Credits
CREATE OR REPLACE FUNCTION hold_credits(
    p_user_id UUID, p_job_id UUID, p_amount INT
) RETURNS void AS $$
DECLARE v_balance INT;
BEGIN
    SELECT credits INTO v_balance FROM users WHERE id = p_user_id FOR UPDATE;
    IF v_balance < p_amount THEN RAISE EXCEPTION 'Insufficient credits'; END IF;
    
    UPDATE users SET credits = credits - p_amount, updated_at = NOW() WHERE id = p_user_id;
    UPDATE jobs SET credits_held = p_amount WHERE id = p_job_id;
    
    INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
    VALUES (p_user_id, p_job_id, 'hold', -p_amount, v_balance - p_amount, 'Hold for job');
END;
$$ LANGUAGE plpgsql VOLATILE;

-- Partial Commit Credits
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

-- Release Credits (Refund all)
CREATE OR REPLACE FUNCTION release_credits(
    p_user_id UUID, p_job_id UUID
) RETURNS void AS $$
DECLARE v_held INT;
BEGIN
    SELECT credits_held INTO v_held FROM jobs WHERE id = p_job_id FOR UPDATE;
    IF v_held IS NULL THEN RAISE EXCEPTION 'Job not found: %', p_job_id; END IF;
    IF v_held > 0 THEN
        UPDATE users SET credits = credits + v_held, updated_at = NOW() WHERE id = p_user_id;
        INSERT INTO credit_transactions (user_id, job_id, action, amount, balance_after, reason)
        VALUES (p_user_id, p_job_id, 'release', v_held, (SELECT credits FROM users WHERE id = p_user_id), 'Release held credits');
        UPDATE jobs SET credits_held = 0 WHERE id = p_job_id;
    END IF;
END;
$$ LANGUAGE plpgsql VOLATILE;