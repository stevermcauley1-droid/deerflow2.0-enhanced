# Jobs2Go Pilot Go-Live Package

This package is the launch-control document for pilot day.

## 1) Objective
Launch a controlled Jobs2Go pilot with verified end-to-end flow:
- job intake
- candidate ranking
- offer and booking lifecycle
- escrow authorization and release
- review and trust reporting
- ops KPI visibility

## 2) Launch Roles
- Launch commander: owns go/no-go decision and timeline.
- API owner: validates backend endpoint health and smoke results.
- Payments owner: validates escrow and ledger checks.
- Trust and safety owner: validates moderation and trust report handling.
- Ops owner: monitors dashboard KPIs and incident channel.

## 3) Pre-Launch Timeline
- T-24h: complete full readiness checklist.
- T-4h: run full smoke flow using pilot cockpit page.
- T-60m: run gate commands and final go/no-go review.
- T-15m: freeze non-launch changes and lock release branch.

## 4) Launch-Day Run Sheet
1. Verify backend service health endpoint.
2. Open pilot cockpit page and run full user flow once.
3. Confirm accepted offer creates booking.
4. Confirm completed booking allows escrow release.
5. Confirm trust report submission and priority classification.
6. Open ops dashboard and verify KPI counters update.
7. Announce pilot open with launch timestamp in ops channel.

PowerShell command for scripted smoke checks:
- `./jobs2go/scripts/smoke_jobs2go_endpoints.ps1`

## 5) Incident Triage Matrix
- Sev1: payment release failure, ledger invariant failure, or complete API outage.
- Sev2: trust report failures, booking lifecycle regression, or persistent matching failures.
- Sev3: UI degradation with functioning APIs.

Response targets:
- Sev1: acknowledge within 5 minutes, mitigation in 15 minutes.
- Sev2: acknowledge within 15 minutes, mitigation in 60 minutes.
- Sev3: acknowledge within 60 minutes, schedule fix same day.

## 6) Rollback Triggers
Trigger rollback immediately if any occur:
- Escrow release path fails for completed booking.
- Ledger invariant check fails.
- Trust report endpoint is unavailable for more than 10 minutes.
- Fill flow cannot complete from offer acceptance to booking completion.

## 7) Rollback Actions
1. Stop pilot intake (disable external access at routing layer).
2. Preserve logs, payment events, and trust events.
3. Switch to last known good deployment.
4. Re-run smoke checks.
5. Resume pilot only after launch commander approval.

## 8) Post-Launch Reporting (Day 1)
- Jobs created
- Offers sent and accepted
- Completion rate
- Escrow authorization count and release rate
- Trust reports and priority reports
- Top 3 friction points and corrective actions

## 9) Go/No-Go Artifact
- Use `jobs2go/GO_NO_GO_SIGNOFF_TEMPLATE.md` as the official decision record.
- A prefilled working draft is available at `jobs2go/GO_NO_GO_SIGNOFF_DRAFT_2026-04-12.md`.
- Record remote workflow confirmation in `jobs2go/CI_CONFIRMATION_LOG_2026-04-12.md`.
