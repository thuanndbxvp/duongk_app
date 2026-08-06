# q18-add-full-name.ps1
# Apply migration 0030: thêm cột full_name vào users
# Run: powershell -File q18-add-full-name.ps1

$ErrorActionPreference = "Stop"

# Load env
$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

if (-not $env:SUPABASE_DB_URL) {
    Write-Host "ERROR: SUPABASE_DB_URL not set. Check .env" -ForegroundColor Red
    exit 1
}

Write-Host "Applying migration 0030_users_full_name.sql..." -ForegroundColor Cyan
psql $env:SUPABASE_DB_URL -f $PSScriptRoot\migrations\0030_users_full_name.sql

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Migration applied. users.full_name added." -ForegroundColor Green
}
