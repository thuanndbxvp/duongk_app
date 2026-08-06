CREATE OR REPLACE FUNCTION revenue_by_day(p_days INT DEFAULT 30) RETURNS TABLE(day DATE, total_credits_consumed BIGINT, total_users BIGINT) AS $body$
BEGIN
  RETURN QUERY
  SELECT
    DATE_TRUNC('day', ct.created_at)::DATE AS day,
    SUM(ABS(ct.amount))::BIGINT,
    COUNT(DISTINCT ct.user_id)::BIGINT
  FROM credit_transactions ct
  WHERE ct.action = 'consume'
    AND ct.created_at >= NOW() - (p_days || ' days')::INTERVAL
    AND p_days > 0
    AND p_days <= 90
  GROUP BY day
  ORDER BY day DESC;
END;
$body$ LANGUAGE plpgsql STABLE;
