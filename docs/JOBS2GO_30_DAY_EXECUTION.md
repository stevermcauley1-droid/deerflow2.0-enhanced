# Jobs2Go 30-Day Execution (One-Step Gated)

This plan is intentionally linear.
Rule: We do exactly one step at a time. No parallel scope expansion.
Gate: We only move to the next step after current step is complete and approved.

## Constraints (Locked)
- Timeline: 30 days
- Launch scope: controlled pilot (not full public rollout)
- Region: one city/region only
- Channels: web only (mobile-responsive), no native apps in phase 1
- Currency/language: single currency and single language
- Matching: rules-based v1 (no advanced ML training loop in phase 1)

## Success Criteria (Pilot)
- Employer can create job and receive shortlist
- Worker can accept offer and complete job
- Escrow authorize/release works reliably
- Reviews captured
- Basic trust controls active (KYC + moderation queue)
- Metrics visible for pilot operations

## Step List
1. Step 1 - Scope lock + acceptance criteria (COMPLETE)
2. Step 2 - Create Jobs2Go workspace skeleton and config (COMPLETE)
3. Step 3 - Add Flyway + Liquibase core migration assets (COMPLETE)
4. Step 4 - Add domain-split OpenAPI package + example payloads (COMPLETE)
5. Step 5 - Scaffold backend modules for pilot flow (COMPLETE)
6. Step 6 - Implement auth/KYC integration interfaces (COMPLETE)
7. Step 7 - Implement jobs + matching v1 endpoints (COMPLETE)
8. Step 8 - Implement offers/bookings lifecycle endpoints (COMPLETE)
9. Step 9 - Implement payments/escrow + ledger invariants (COMPLETE)
10. Step 10 - Implement chat/reviews/trust endpoints (COMPLETE)
11. Step 11 - Add frontend pilot flows (employer + worker web) (COMPLETE)
12. Step 12 - Add ops views + pilot KPI dashboard (COMPLETE)
13. Step 13 - Add tests, CI gates, and production hardening checks (COMPLETE)
14. Step 14 - Pilot readiness checklist + go-live package (COMPLETE)

## Completion Protocol
For each step:
1. Define exact deliverable
2. Implement only that deliverable
3. Run verification checks
4. Report result
5. Wait for your explicit approval before next step
