CREATE OR REPLACE FUNCTION create_alert(p_severity TEXT, p_category TEXT, p_message TEXT, p_context JSONB DEFAULT '{}'::jsonb) RETURNS UUID AS $body$
DECLARE v_id UUID; v_context_hash TEXT;
BEGIN
  v_context_hash := md5(p_context::text);
  IF EXISTS (SELECT 1 FROM admin_alerts WHERE category = p_category AND resolved_at IS NULL AND md5(context::text) = v_context_hash AND created_at > NOW() - INTERVAL '1 hour') THEN
    SELECT id INTO v_id FROM admin_alerts WHERE category = p_category AND resolved_at IS NULL AND md5(context::text) = v_context_hash LIMIT 1;
    RETURN v_id;
  END IF;
  INSERT INTO admin_alerts (severity, category, message, context) VALUES (p_severity, p_category, p_message, p_context) RETURNING id INTO v_id;
  RETURN v_id;
END;
$body$ LANGUAGE plpgsql;
