# Jobs2Go Workspace

This folder contains the standalone Jobs2Go pilot assets.

## Purpose
- Keep migrations, API contracts, and implementation artifacts grouped.
- Support the 30-day one-step gated delivery process.

## Initial Structure
- `config/` environment and service configuration templates
- `migrations/flyway/` Flyway SQL migrations
- `migrations/liquibase/changesets/` Liquibase changesets
- `openapi/domains/` domain-split OpenAPI files
- `openapi/examples/` request/response payload examples
- `scripts/` utility scripts for local validation

## Notes
This workspace starts with skeleton assets only.
Functional migrations and API specs are added in later gated steps.

## Launch Documents
- `PILOT_READINESS_CHECKLIST.md`
- `PILOT_GO_LIVE_PACKAGE.md`
- `LAUNCH_DAY_COMMANDS.md`
- `HARDENING_CHECKS.md`
- `LAUNCH_READINESS_REPORT_2026-04-12.md`
