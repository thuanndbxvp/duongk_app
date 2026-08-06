[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
$token = "YOUR_SUPABASE_SERVICE_ROLE_KEY"

function Run-SQL($sql, $label) {
  $escaped = $sql -replace '\\', '\\' -replace '"', '\"' -replace "`r`n", '\n' -replace "`n", '\n' -replace "`t", '\t'
  $payload = '{"query":"' + $escaped + '"}'
  $wc = New-Object System.Net.WebClient
  $wc.Headers.Add("Authorization", "Bearer $token")
  $wc.Headers.Add("Content-Type", "application/json")
  try {
    $resp = $wc.UploadString("https://api.supabase.com/v1/projects/ctjnnnnikarsaezlkpse/database/query", $payload)
    Write-Host "=== $label ==="
    Write-Host $resp
  } catch [System.Net.WebException] {
    $status = [int]$_.Exception.Response.StatusCode
    $stream = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    Write-Host "=== $label STATUS=$status ==="
    Write-Host $reader.ReadToEnd()
  } finally {
    $wc.Dispose()
  }
  Start-Sleep -Milliseconds 500
}

Run-SQL "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name IN ('role', 'max_assistants', 'banned_at', 'deleted_at', 'last_sign_in_at', 'full_name') ORDER BY column_name;" 'Q14a-users-cols'
Run-SQL "SELECT t.table_name, EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = t.table_name) AS tbl_exists FROM (VALUES ('admin_audit_logs'),('admin_alerts'),('api_provider_keys'),('api_usage_logs'),('service_routing_config'),('mfa_challenges'),('mfa_backup_codes')) AS t(table_name) ORDER BY t.table_name;" 'Q14b-tables'
Run-SQL "SELECT feature, primary_provider, fallback_chain::text, enabled_providers::text FROM service_routing_config ORDER BY feature;" 'Q14c-routing'
Run-SQL "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name IN ('admin_adjust_credits','soft_delete_user','create_alert','record_mfa_failure','revenue_by_day','cohort_retention','top_creators','notify_routing_update') ORDER BY routine_name;" 'Q14d-funcs'
