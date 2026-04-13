# Jobs2Go Pilot Readiness Checklist

Use this checklist 24 hours before launch and again at T-60 minutes.

## 1) Scope Lock Verification
- Pilot region is fixed to one city/region.
- Supported categories are fixed and documented.
- Single language and single currency are configured.
- Web-only pilot scope is confirmed (no native app commitments).

## 2) Backend and API Readiness
- All Jobs2Go v1 routes return expected status in smoke checks.
- Jobs, matching, offers/bookings, payments, and trust endpoints are reachable.
- Ops endpoints are reachable: `/v1/ops/modules` and `/v1/ops/kpi`.
- No unresolved backend diagnostics in Jobs2Go router modules.

## 3) Data and Migrations
- Flyway migration is present and versioned.
- Liquibase changelog and changeset are present and aligned to Flyway SQL.
- OpenAPI domain files are present and synchronized with implemented routes.
- JSON example payload validation passes.

## 4) Security and Trust Baseline
- KYC flow endpoint is enabled and returning provider session URL.
- Escrow-only flow is enforced for payment operations.
- Trust report endpoint accepts and prioritizes high-risk reasons.
- Basic message moderation is active (clear/flagged/blocked states).

## 5) Financial Control Checks
- Escrow authorization succeeds for accepted bookings.
- Escrow release is blocked unless booking is completed.
- Ledger invariant is enforced: debits equal credits for each payment event.
- Payment retrieval endpoint returns final escrow state.

## 6) Ops and Monitoring
- Ops dashboard page loads and refreshes successfully.
- Module health panel reports all Jobs2Go modules active.
- KPI counters reflect end-to-end flow activity.
- On-call owners and escalation contacts are assigned.

## 7) Release Gate Commands
- Run `cd backend && make gate-jobs2go`.
- Run `cd backend && make lint && make test`.
- Run `uv run python jobs2go/scripts/validate_openapi_examples.py` from backend root context.
- On Windows PowerShell, run `./jobs2go/scripts/run_local_launch_gates.ps1` from repo root.
- Confirm `.github/workflows/jobs2go-pilot-gates.yml` is green on the target PR.

## 8) Go/No-Go Criteria
- Go if all gate commands pass and no Sev1/Sev2 open incidents exist.
- No-Go if payment release path fails or ledger invariant fails.
- No-Go if trust report endpoint is unavailable.
- No-Go if ops KPI dashboard cannot refresh during smoke test.

## 9) Sign-Off
- Product owner sign-off.
- Engineering owner sign-off.
- Trust and safety owner sign-off.
- Operations/on-call owner sign-off.
- Record final decision in `jobs2go/GO_NO_GO_SIGNOFF_TEMPLATE.md`.
