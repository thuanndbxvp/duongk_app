CREATE OR REPLACE FUNCTION admin_adjust_credits(p_admin_id UUID, p_user_id UUID, p_delta INT, p_reason TEXT) RETURNS TABLE(new_balance INT, tx_id UUID) AS $body$
DECLARE v_current INT; v_tx_id UUID;
BEGIN
  IF p_reason IS NULL OR length(trim(p_reason)) < 10 THEN RAISE EXCEPTION 'Reason required (min 10 chars)'; END IF;
  SELECT credits INTO v_current FROM users WHERE id = p_user_id FOR UPDATE;
  IF v_current IS NULL THEN RAISE EXCEPTION 'User not found'; END IF;
  UPDATE users SET credits = credits + p_delta, updated_at = NOW() WHERE id = p_user_id;
  INSERT INTO credit_transactions (user_id, action, amount, balance_after, reason, metadata) VALUES (p_user_id, 'admin_adjust', p_delta, v_current + p_delta, p_reason, jsonb_build_object('admin_id', p_admin_id)) RETURNING id INTO v_tx_id;
  RETURN QUERY SELECT v_current + p_delta, v_tx_id;
END;
$body$ LANGUAGE plpgsql;
