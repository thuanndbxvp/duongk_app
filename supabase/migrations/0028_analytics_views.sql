-- ============================================================
-- Migration: 0028_analytics_views.sql
-- Purpose: Analytics RPC functions (cohort retention, revenue, top creators)
-- ============================================================

-- Index: optimize credit_transactions queries by created_at
CREATE INDEX IF NOT EXISTS idx_credit_tx_created ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_tx_action_created ON credit_transactions(action, created_at DESC);

-- RPC 1: revenue_by_day(days INT DEFAULT 30)
-- Returns: list of {day, total_credits_consumed, total_users}
CREATE OR REPLACE FUNCTION revenue_by_day(p_days INT DEFAULT 30)
RETURNS TABLE(day DATE, total_credits_consumed BIGINT, total_users BIGINT) AS $$
BEGIN
  RETURN QUERY
  SELECT
    DATE_TRUNC('day', ct.created_at)::DATE AS day,
    SUM(ABS(ct.amount))::BIGINT AS total_credits_consumed,
    COUNT(DISTINCT ct.user_id)::BIGINT AS total_users
  FROM credit_transactions ct
  WHERE ct.action = 'consume'
    AND ct.created_at >= NOW() - (p_days || ' days')::INTERVAL
    AND p_days > 0
    AND p_days <= 90
  GROUP BY day
  ORDER BY day DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- RPC 2: cohort_retention(cohort_weeks INT DEFAULT 8)
-- Cohort = week of user signup (Monday)
-- Returns: list of {cohort_week, week_offset, active_users, cohort_size, retention_pct}
CREATE OR REPLACE FUNCTION cohort_retention(p_cohort_weeks INT DEFAULT 8)
RETURNS TABLE(
  cohort_week DATE,
  week_offset INT,
  active_users BIGINT,
  cohort_size BIGINT,
  retention_pct NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  WITH cohorts AS (
    SELECT
      DATE_TRUNC('week', u.created_at)::DATE AS cohort_week,
      u.id AS user_id
    FROM users u
    WHERE u.created_at >= NOW() - (p_cohort_weeks || ' weeks')::INTERVAL
  ),
  cohort_sizes AS (
    SELECT cohort_week, COUNT(*) AS cohort_size
    FROM cohorts
    GROUP BY cohort_week
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
    AND act.created_at >= c.cohort_week + (act.created_at - c.cohort_week)  -- any week after signup
  GROUP BY c.cohort_week, week_offset, cs.cohort_size
  HAVING EXTRACT(WEEK FROM AGE(act.created_at, c.cohort_week))::INT >= 0
    AND EXTRACT(WEEK FROM AGE(act.created_at, c.cohort_week))::INT < p_cohort_weeks
  ORDER BY c.cohort_week DESC, week_offset ASC
  LIMIT p_cohort_weeks * p_cohort_weeks;
END;
$$ LANGUAGE plpgsql STABLE;

-- RPC 3: top_creators(metric TEXT DEFAULT 'assistants', max_limit INT DEFAULT 10)
-- metric: 'assistants' | 'credits_consumed'
-- Returns: list of {user_id, email, metric_value, tier, created_at}
CREATE OR REPLACE FUNCTION top_creators(p_metric TEXT DEFAULT 'assistants', p_limit INT DEFAULT 10)
RETURNS TABLE(
  user_id UUID,
  email TEXT,
  metric_value BIGINT,
  tier TEXT,
  created_at TIMESTAMPTZ
) AS $$
BEGIN
  IF p_metric = 'assistants' THEN
    RETURN QUERY
    SELECT
      u.id,
      u.email,
      COUNT(ca.id)::BIGINT AS metric_value,
      u.tier,
      u.created_at
    FROM users u
    LEFT JOIN channel_assistants ca ON ca.user_id = u.id
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COUNT(ca.id) > 0
    ORDER BY metric_value DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSIF p_metric = 'credits_consumed' THEN
    RETURN QUERY
    SELECT
      u.id,
      u.email,
      COALESCE(SUM(ABS(ct.amount)), 0)::BIGINT AS metric_value,
      u.tier,
      u.created_at
    FROM users u
    LEFT JOIN credit_transactions ct ON ct.user_id = u.id AND ct.action = 'consume'
    GROUP BY u.id, u.email, u.tier, u.created_at
    HAVING COALESCE(SUM(ABS(ct.amount)), 0) > 0
    ORDER BY metric_value DESC, u.created_at DESC
    LIMIT GREATEST(LEAST(p_limit, 100), 1);
  ELSE
    RETURN;
  END IF;
END;
$$ LANGUAGE plpgsql STABLE;