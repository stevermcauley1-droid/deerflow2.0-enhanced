param(
    [string]$ApiBase = "http://localhost:8001",
    [string]$AppBase = "http://localhost:2026",
    [int]$TimeoutSec = 30,
    [switch]$SkipUi
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Test-Endpoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec $TimeoutSec -UseBasicParsing
        $code = [int]$response.StatusCode
        if ($code -lt 200 -or $code -ge 300) {
            throw "Unexpected status code $code"
        }
        Write-Host "[PASS] $Name -> $Url ($code)" -ForegroundColor Green
    }
    catch {
        Write-Host "[FAIL] $Name -> $Url" -ForegroundColor Red
        throw "Smoke check failed for '$Name'. Ensure the service is running and reachable at '$Url'. For backend startup, confirm config.yaml exists and start the gateway before running smoke checks. If using Next.js dev mode, first route compilation may need a longer timeout (use -TimeoutSec)."
    }
}

Write-Host "[Jobs2Go] Running smoke checks..." -ForegroundColor Cyan
Write-Host "API base: $ApiBase"
if (-not $SkipUi) {
    Write-Host "App base: $AppBase"
}

Test-Endpoint -Name "Backend health" -Url "$ApiBase/health"
Test-Endpoint -Name "Ops modules" -Url "$ApiBase/v1/ops/modules"
Test-Endpoint -Name "Ops KPI" -Url "$ApiBase/v1/ops/kpi"

if (-not $SkipUi) {
    Test-Endpoint -Name "Pilot cockpit page" -Url "$AppBase/jobs2go"
    Test-Endpoint -Name "Ops dashboard page" -Url "$AppBase/jobs2go/ops"
}

Write-Host "[Jobs2Go] Smoke checks passed." -ForegroundColor Green
