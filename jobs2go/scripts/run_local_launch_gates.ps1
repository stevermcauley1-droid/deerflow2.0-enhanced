$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$ErrorMessage (exit code: $LASTEXITCODE)"
    }
}

Write-Host "[Jobs2Go] Running local launch gates..." -ForegroundColor Cyan

Push-Location (Join-Path $PSScriptRoot "..\..")
try {
    Push-Location "backend"
    try {
        Write-Host "[1/5] Backend deps sync" -ForegroundColor Yellow
        Invoke-External "uv sync --group dev" "Backend dependency sync failed"

        Write-Host "[2/5] Jobs2Go gate (routers + focused tests)" -ForegroundColor Yellow
        Invoke-External "uvx ruff check app/gateway/routers/jobs2go_*.py tests/test_jobs2go_pilot_services.py" "Jobs2Go Ruff gate failed"
        $env:PYTHONPATH = "."
        Invoke-External "uv run pytest tests/test_jobs2go_pilot_services.py -c pyproject.toml -v" "Jobs2Go focused tests failed"

        Write-Host "[3/5] Full backend lint + tests" -ForegroundColor Yellow
        Invoke-External "uvx ruff check ." "Full backend Ruff checks failed"
        Invoke-External "uv run pytest tests -c pyproject.toml -q" "Full backend tests failed"
    }
    finally {
        Pop-Location
    }

    Write-Host "[4/5] OpenAPI examples validation" -ForegroundColor Yellow
    Invoke-External "uv run python jobs2go/scripts/validate_openapi_examples.py" "OpenAPI example validation failed"

    Push-Location "frontend"
    try {
        Write-Host "[5/5] Frontend lint + typecheck" -ForegroundColor Yellow
        Invoke-External "pnpm lint" "Frontend lint failed"
        Invoke-External "pnpm typecheck" "Frontend typecheck failed"
    }
    finally {
        Pop-Location
    }

    Write-Host "[Jobs2Go] All local launch gates passed." -ForegroundColor Green
}
finally {
    Pop-Location
}
