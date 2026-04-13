# Jobs2Go Go-No-Go Sign-Off Template

Date: YYYY-MM-DD
Release candidate: <branch-or-tag>
Launch window: <time-range>
Launch commander: <name>

## Gate Evidence
- Local gate script result: PASS | FAIL
- Launch readiness report: jobs2go/LAUNCH_READINESS_REPORT_2026-04-12.md
- Backend CI workflow (.github/workflows/backend-unit-tests.yml): PASS | FAIL | PENDING
- Jobs2Go CI workflow (.github/workflows/jobs2go-pilot-gates.yml): PASS | FAIL | PENDING

## Risk Check
- Sev1 incidents open: YES | NO
- Sev2 incidents open: YES | NO
- Payment release and ledger invariant verified: YES | NO
- Trust report path verified: YES | NO
- Ops dashboard refresh verified: YES | NO

## Decision
Decision: GO | NO-GO
Decision time: HH:MM TZ
Notes: <free text>

## Owner Sign-Offs
- Product owner: <name> - GO | NO-GO - <timestamp>
- Engineering owner: <name> - GO | NO-GO - <timestamp>
- Trust and safety owner: <name> - GO | NO-GO - <timestamp>
- Operations owner: <name> - GO | NO-GO - <timestamp>
