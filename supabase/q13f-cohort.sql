CREATE OR REPLACE FUNCTION cohort_retention(p_cohort_weeks INT DEFAULT 8) RETURNS TABLE(cohort_week DATE, week_offset INT, active_users BIGINT, cohort_size BIGINT, retention_pct NUMERIC) AS $body$
BEGIN
  RETURN QUERY
  WITH cohorts AS (
    SELECT DATE_TRUNC('week', u.created_at)::DATE AS cohort_week, u.id AS user_id
    FROM users u
    WHERE u.created_at >= NOW() - (p_cohort_weeks || ' weeks')::INTERVAL
  ),
  cohort_sizes AS (
    SELECT cohort_week, COUNT(*) AS cohort_size FROM cohorts GROUP BY cohort_week
  )
  SELECT
    c.cohort_week,
    EXTRACT(WEEK FROM AGE(act.created_at, c.cohort_week))::INT AS week_offset,
    COUNT(DISTINCT act.user_id)::BIGINT AS active_users,
    cs.cohort_size::BIGINT,
    ROUND(COUNT(DISTINCT act.user_id)::NUMERIC / NULLIF(cs.cohort_size, 0), 4) AS retention_pct
  FROM cohorts c
  JOIN cohort_sizes cs ON c.cohort_week = cs.cohort_week
  LEFT JOIN credit_transactions act ON act.user_id = c.user_id
  GROUP BY c.cohort_week, week_offset, cs.cohort_size
  ORDER BY c.cohort_week DESC, week_offset ASC
  LIMIT p_cohort_weeks * p_cohort_weeks;
END;
$body$ LANGUAGE plpgsql STABLE;
