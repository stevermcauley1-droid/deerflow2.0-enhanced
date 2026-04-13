# Jobs2Go Launch Day Commands

Run commands from repository root unless stated otherwise.

Prerequisite: ensure `config.yaml` exists at repo root and services are started before smoke checks.

## 1) Backend Gate
```bash
cd backend
make gate-jobs2go
```

Windows PowerShell equivalent from repo root:
```powershell
./jobs2go/scripts/run_local_launch_gates.ps1
```

## 2) Full Backend Validation
```bash
cd backend
make lint
make test
```

## 3) OpenAPI Example Validation
```bash
cd backend
uv run python ../jobs2go/scripts/validate_openapi_examples.py
```

## 4) Start Full Local Stack (optional smoke environment)
```bash
make dev
```

Windows gateway-only startup (if running API smoke only):
```powershell
cd backend
$env:PYTHONPATH='.'
uv run uvicorn app.gateway.app:app --host 127.0.0.1 --port 8001
```

## 5) Smoke Endpoints
- Health: `GET /health`
- Pilot cockpit page: `/jobs2go`
- Ops dashboard page: `/jobs2go/ops`
- Ops modules: `GET /v1/ops/modules`
- Ops KPI snapshot: `GET /v1/ops/kpi`

Windows PowerShell smoke script from repo root:
```powershell
./jobs2go/scripts/smoke_jobs2go_endpoints.ps1
```

API-only smoke mode (if frontend/nginx not started):
```powershell
./jobs2go/scripts/smoke_jobs2go_endpoints.ps1 -SkipUi
```

## 6) Stop Stack
```bash
make stop
```

## 7) Sign-Off Record
- Fill `jobs2go/GO_NO_GO_SIGNOFF_TEMPLATE.md` during the T-60m go/no-go call.
