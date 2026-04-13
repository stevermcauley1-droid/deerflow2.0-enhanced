"""Payments and escrow service with ledger invariants for Jobs2Go pilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.gateway.routers.jobs2go_offers_service import offers_bookings_store


@dataclass
class PaymentRecord:
    id: str
    booking_id: str
    employer_id: str
    worker_id: str
    payment_method_id: str
    currency: str
    gross_amount_cents: int
    platform_fee_cents: int
    worker_payout_cents: int
    escrow_status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class LedgerEntry:
    id: str
    payment_id: str
    booking_id: str
    account_code: str
    direction: str
    amount_cents: int
    currency: str
    event_type: str
    created_at: datetime


class InMemoryPaymentsStore:
    def __init__(self, booking_store=None) -> None:
        self._payments_by_id: dict[str, PaymentRecord] = {}
        self._payments_by_booking_id: dict[str, PaymentRecord] = {}
        self._ledger_entries_by_payment_id: dict[str, list[LedgerEntry]] = {}
        self._booking_store = booking_store or offers_bookings_store

    async def authorize_escrow(
        self,
        booking_id: str,
        payment_method_id: str,
        amount_cents: int,
        currency: str,
    ) -> PaymentRecord:
        if amount_cents <= 0:
            raise ValueError("invalid_amount")

        booking = await self._booking_store.get_booking_by_id(booking_id)
        if booking is None:
            raise ValueError("booking_not_found")

        existing = self._payments_by_booking_id.get(booking_id)
        if existing is not None and existing.escrow_status in {"authorized", "released"}:
            raise ValueError("payment_already_exists")

        platform_fee_cents = int(round(amount_cents * 0.15))
        worker_payout_cents = amount_cents - platform_fee_cents

        payment = PaymentRecord(
            id=str(uuid4()),
            booking_id=booking_id,
            employer_id=booking.employer_id,
            worker_id=booking.worker_id,
            payment_method_id=payment_method_id,
            currency=currency,
            gross_amount_cents=amount_cents,
            platform_fee_cents=platform_fee_cents,
            worker_payout_cents=worker_payout_cents,
            escrow_status="authorized",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        authorize_entries = [
            LedgerEntry(
                id=str(uuid4()),
                payment_id=payment.id,
                booking_id=booking_id,
                account_code="CASH_CLEARING",
                direction="debit",
                amount_cents=amount_cents,
                currency=currency,
                event_type="escrow_authorized",
                created_at=datetime.now(UTC),
            ),
            LedgerEntry(
                id=str(uuid4()),
                payment_id=payment.id,
                booking_id=booking_id,
                account_code="ESCROW_LIABILITY",
                direction="credit",
                amount_cents=amount_cents,
                currency=currency,
                event_type="escrow_authorized",
                created_at=datetime.now(UTC),
            ),
        ]
        _assert_ledger_balanced(authorize_entries)

        self._payments_by_id[payment.id] = payment
        self._payments_by_booking_id[booking_id] = payment
        self._ledger_entries_by_payment_id[payment.id] = authorize_entries
        return payment

    async def release_escrow(self, booking_id: str) -> PaymentRecord:
        booking = await self._booking_store.get_booking_by_id(booking_id)
        if booking is None:
            raise ValueError("booking_not_found")

        payment = self._payments_by_booking_id.get(booking_id)
        if payment is None:
            raise ValueError("payment_not_found")
        if payment.escrow_status != "authorized":
            raise ValueError("invalid_payment_state")
        if booking.status != "completed":
            raise ValueError("booking_not_completed")

        release_entries = [
            LedgerEntry(
                id=str(uuid4()),
                payment_id=payment.id,
                booking_id=booking_id,
                account_code="ESCROW_LIABILITY",
                direction="debit",
                amount_cents=payment.gross_amount_cents,
                currency=payment.currency,
                event_type="escrow_released",
                created_at=datetime.now(UTC),
            ),
            LedgerEntry(
                id=str(uuid4()),
                payment_id=payment.id,
                booking_id=booking_id,
                account_code="WORKER_PAYABLE",
                direction="credit",
                amount_cents=payment.worker_payout_cents,
                currency=payment.currency,
                event_type="escrow_released",
                created_at=datetime.now(UTC),
            ),
            LedgerEntry(
                id=str(uuid4()),
                payment_id=payment.id,
                booking_id=booking_id,
                account_code="PLATFORM_REVENUE",
                direction="credit",
                amount_cents=payment.platform_fee_cents,
                currency=payment.currency,
                event_type="escrow_released",
                created_at=datetime.now(UTC),
            ),
        ]
        _assert_ledger_balanced(release_entries)

        existing = self._ledger_entries_by_payment_id.get(payment.id, [])
        self._ledger_entries_by_payment_id[payment.id] = [*existing, *release_entries]

        payment.escrow_status = "released"
        payment.updated_at = datetime.now(UTC)
        return payment

    async def get_payment(self, payment_id: str) -> PaymentRecord | None:
        return self._payments_by_id.get(payment_id)

    async def list_payments(self) -> list[PaymentRecord]:
        return list(self._payments_by_id.values())

    def reset(self) -> None:
        self._payments_by_id.clear()
        self._payments_by_booking_id.clear()
        self._ledger_entries_by_payment_id.clear()



def _assert_ledger_balanced(entries: list[LedgerEntry]) -> None:
    debits = sum(entry.amount_cents for entry in entries if entry.direction == "debit")
    credits = sum(entry.amount_cents for entry in entries if entry.direction == "credit")
    if debits != credits:
        raise ValueError("ledger_unbalanced")


payments_store = InMemoryPaymentsStore()
