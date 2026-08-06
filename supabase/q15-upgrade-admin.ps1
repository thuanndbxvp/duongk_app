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

# 1) Check current state of nobita6986
Run-SQL "SELECT id, email, role, tier, credits, deleted_at FROM users WHERE email = 'nobita6986@gmail.com';" 'CURRENT-state'

# 2) Force clean single TEXT column (idempotent)
Run-SQL "DO \$\$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role' AND data_type = 'character varying') THEN ALTER TABLE users DROP COLUMN role; END IF; END \$\$;" 'FIX-drop-varchar'
Run-SQL "ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin', 'super_admin'));" 'FIX-add-text'

# 3) Verify column is now single TEXT
Run-SQL "SELECT column_name, data_type, column_default, is_nullable FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role';" 'VERIFY-role-col'

# 4) Upgrade nobita6986 to super_admin
Run-SQL "UPDATE users SET role = 'super_admin', updated_at = NOW() WHERE email = 'nobita6986@gmail.com' AND deleted_at IS NULL RETURNING id, email, role, tier, credits;" 'UPGRADE-admin'

# 5) Final verify
Run-SQL "SELECT id, email, role, tier, credits, created_at FROM users WHERE email = 'nobita6986@gmail.com';" 'FINAL-verify'
