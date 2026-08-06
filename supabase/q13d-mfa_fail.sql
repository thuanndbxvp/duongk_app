CREATE OR REPLACE FUNCTION record_mfa_failure(p_user_id UUID) RETURNS VOID AS $body$
BEGIN
  UPDATE mfa_challenges SET failed_attempts = failed_attempts + 1, locked_until = CASE WHEN failed_attempts + 1 >= 5 THEN NOW() + INTERVAL '15 minutes' ELSE locked_until END, updated_at = NOW() WHERE user_id = p_user_id AND status = 'active';
END;
$body$ LANGUAGE plpgsql;
