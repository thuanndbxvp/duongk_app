CREATE OR REPLACE FUNCTION top_creators(p_metric TEXT DEFAULT 'assistants', p_limit INT DEFAULT 10) RETURNS TABLE(user_id UUID, email TEXT, metric_value BIGINT, tier TEXT, created_at TIMESTAMPTZ) AS $body$
BEGIN
  IF p_metric = 'assistants' THEN
    RETURN QUERY
    SELECT u.id, u.email, COUNT(ca.id)::BIGINT, u.tier, u.created_at
    FROM users u
    LEFT JOIN channel_assistants ca ON ca.user_id = u.id
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COUNT(ca.id) > 0
    ORDER BY COUNT(ca.id) DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSIF p_metric = 'credits_consumed' THEN
    RETURN QUERY
    SELECT u.id, u.email, COALESCE(SUM(ABS(ct.amount)), 0)::BIGINT, u.tier, u.created_at
    FROM users u
    LEFT JOIN credit_transactions ct ON ct.user_id = u.id AND ct.action = 'consume'
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COALESCE(SUM(ABS(ct.amount)), 0) > 0
    ORDER BY COALESCE(SUM(ABS(ct.amount)), 0) DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSE
    RETURN;
  END IF;
END;
$body$ LANGUAGE plpgsql STABLE;
