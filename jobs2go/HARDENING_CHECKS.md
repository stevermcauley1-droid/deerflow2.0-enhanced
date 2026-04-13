# Jobs2Go Production Hardening Checks

These checks are required before pilot go-live.

## Security
- Replace pilot password hashing with Argon2 or bcrypt.
- Add JWT signing key rotation and token expiry enforcement.
- Enforce authentication and role checks on all `v1` endpoints.
- Add rate limits on auth, offer, payments, and trust-report endpoints.
- Add request-id tracing and immutable audit event logging.

## Payments and Ledger
- Persist payments and ledger entries in PostgreSQL.
- Enforce idempotency keys on escrow authorize and release endpoints.
- Add reconciliation job against payment provider settlement files.
- Add alert on any ledger imbalance event.

## Reliability and Operations
- Move in-memory stores to repository-backed persistence.
- Add retry policies and timeout budgets for KYC and payment providers.
- Add dashboard alerts for fill-rate drop, payout failure, and trust surge.
- Add rollback playbook with deployment and data rollback strategy.

## Compliance and Policy
- Add data retention rules for chat, trust reports, and verification artifacts.
- Add PII redaction policy for logs and analytics exports.
- Validate jurisdiction-specific KYC and labor policy settings.

## Required Verification Commands
- `cd backend && make gate-jobs2go`
- `python jobs2go/scripts/validate_openapi_examples.py`
- `cd backend && make lint && make test`
