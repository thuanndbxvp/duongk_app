#!/usr/bin/env pwsh
# ============================================================
# Smoke test cho 42 admin routes — verify route có response
# (không phải 404 / import error / Python exception).
#
# Usage:
#   pwsh scripts/admin_smoke_test.ps1 -ApiBase "http://localhost:8000"
#
# Lưu ý: Script này CHỈ verify routes mount đúng + endpoint không crash.
#        Để test business logic (RLS, RBAC) cần service_role key + test DB.
# ============================================================

param(
    [string]$ApiBase = "http://localhost:8000",
    [int]$Timeout = 10
)

$ErrorActionPreference = "Stop"
$results = @()

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Admin Panel Smoke Test" -ForegroundColor Cyan
Write-Host "  ApiBase: $ApiBase" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1) Health check
Write-Host "[1/3] Checking FastAPI app is alive..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$ApiBase/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ /health → $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ /health failed: $_" -ForegroundColor Red
    Write-Host "  → Make sure uvicorn is running: cd apps/api; uvicorn apps.api.main:app --port 8000" -ForegroundColor Yellow
    exit 1
}

# 2) List admin routes từ FastAPI
Write-Host ""
Write-Host "[2/3] Listing admin routes from FastAPI..." -ForegroundColor Yellow
$adminRoutes = & python scripts/list_admin_routes.py 2>$null | Where-Object { $_ -match '\|/api/admin' }

if (-not $adminRoutes -or $adminRoutes.Count -eq 0) {
    Write-Host "  ✗ No admin routes found (run from D:\appDK)" -ForegroundColor Red
    exit 1
}

Write-Host "  Found $($adminRoutes.Count) admin routes" -ForegroundColor Green
Write-Host ""

# 3) Smoke test mỗi route — expect 401/403 (auth required) hoặc 200 (nếu không yêu cầu auth)
Write-Host "[3/3] Smoke testing routes (expect 401/403/200, NOT 404/500)..." -ForegroundColor Yellow
Write-Host ""

$ok = 0
$expected = $adminRoutes.Count
$failed = @()

foreach ($line in $adminRoutes) {
    $parts = $line -split '\|'
    $method = $parts[0]
    $path = $parts[1]

    # Replace path params với placeholder UUID
    $testPath = $path -replace '\{[^}]+\}', '00000000-0000-0000-0000-000000000000'

    $url = "$ApiBase$testPath"
    $passed = $false
    $status = 0
    $body = ""

    try {
        $response = Invoke-WebRequest -Uri $url -Method $method -TimeoutSec $Timeout -UseBasicParsing -ErrorAction Stop
        $status = $response.StatusCode
        $body = $response.Content
        # Accept 200, 401 (no auth), 403 (not admin), 422 (validation), 405 (method not allowed)
        if ($status -in 200, 401, 403, 422, 405) {
            $passed = $true
            $ok++
        }
    }
    catch {
        $ex = $_.Exception.Response
        if ($ex) {
            $status = [int]$ex.StatusCode
        } else {
            $status = 0
        }
        if ($status -in 200, 401, 403, 422, 405) {
            $passed = $true
            $ok++
        } else {
            $failed += [PSCustomObject]@{
                Method = $method
                Path = $path
                Status = $status
                Error = $_.Exception.Message
            }
        }
    }

    $color = if ($passed) { "Green" } else { "Red" }
    $statusColor = if ($status -eq 200) { "Green" }
                   elseif ($status -in 401, 403) { "Yellow" }
                   elseif ($status -eq 422) { "Cyan" }
                   elseif ($status -in 404, 500, 502, 503) { "Red" }
                   else { "White" }
    Write-Host ("  {0,-6} {1,-55} → {2}" -f $method, $path, $status) -ForegroundColor $statusColor
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Results: $ok / $expected passed" -ForegroundColor $(if ($ok -eq $expected) { "Green" } else { "Yellow" })
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($failed.Count -gt 0) {
    Write-Host "Failed routes:" -ForegroundColor Red
    foreach ($f in $failed) {
        Write-Host "  $($f.Method) $($f.Path) → $($f.Status)" -ForegroundColor Red
        Write-Host "    $($f.Error)" -ForegroundColor DarkRed
    }
    exit 1
}

Write-Host "All admin routes mounted correctly." -ForegroundColor Green
