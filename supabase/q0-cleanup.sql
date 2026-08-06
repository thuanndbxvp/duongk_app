-- ============================================================
-- Q0: DROP STALE VIEW + OBJECT (chạy 1 lần đầu tiên)
-- Sếp paste đoạn này trước, RUN, xong rồi mới paste phần còn lại.
-- ============================================================
DROP VIEW IF EXISTS api_usage_summary CASCADE;
DROP TABLE IF EXISTS api_usage_logs CASCADE;
DROP FUNCTION IF EXISTS notify_routing_update() CASCADE;
DROP TRIGGER IF EXISTS trigger_routing_update ON service_routing_config;
DROP TABLE IF EXISTS service_routing_config CASCADE;
DROP TABLE IF EXISTS mfa_backup_codes CASCADE;
DROP TABLE IF EXISTS mfa_challenges CASCADE;
DROP TABLE IF EXISTS admin_alerts CASCADE;
DROP TABLE IF EXISTS api_provider_keys CASCADE;
DROP TABLE IF EXISTS admin_audit_logs CASCADE;
