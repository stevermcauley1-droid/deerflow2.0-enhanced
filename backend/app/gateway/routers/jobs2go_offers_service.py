"""Offers and bookings lifecycle service for Jobs2Go pilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.gateway.routers.jobs2go_jobs_service import jobs_store


@dataclass
class OfferRecord:
    id: str
    job_id: str
    worker_id: str
    message: str | None
    proposed_amount_cents: int
    currency: str
    status: str
    expires_at: datetime | None
    responded_at: datetime | None
    created_at: datetime


@dataclass
class BookingRecord:
    id: str
    job_id: str
    offer_id: str
    employer_id: str
    worker_id: str
    status: str
    starts_at: datetime | None
    ended_at: datetime | None
    completion_notes: str | None
    created_at: datetime
    updated_at: datetime


class InMemoryOffersBookingsStore:
    def __init__(self, jobs_repository=None) -> None:
        self._offers_by_id: dict[str, OfferRecord] = {}
        self._bookings_by_job_id: dict[str, BookingRecord] = {}
        self._bookings_by_id: dict[str, BookingRecord] = {}
        self._jobs_repository = jobs_repository or jobs_store

    async def create_offer(
        self,
        job_id: str,
        worker_id: str,
        message: str | None,
        proposed_amount_cents: int,
        currency: str,
        expires_at: datetime | None,
    ) -> OfferRecord:
        job = await self._jobs_repository.get_job(job_id)
        if job is None:
            raise ValueError("job_not_found")

        if proposed_amount_cents < 0:
            raise ValueError("invalid_amount")

        offer = OfferRecord(
            id=str(uuid4()),
            job_id=job_id,
            worker_id=worker_id,
            message=message,
            proposed_amount_cents=proposed_amount_cents,
            currency=currency,
            status="pending",
            expires_at=expires_at,
            responded_at=None,
            created_at=datetime.now(UTC),
        )
        self._offers_by_id[offer.id] = offer
        return offer

    async def accept_offer(self, offer_id: str) -> OfferRecord:
        offer = self._offers_by_id.get(offer_id)
        if offer is None:
            raise ValueError("offer_not_found")
        if offer.status != "pending":
            raise ValueError("offer_not_pending")

        offer.status = "accepted"
        offer.responded_at = datetime.now(UTC)

        job = await self._jobs_repository.get_job(offer.job_id)
        if job is None:
            raise ValueError("job_not_found")

        booking = BookingRecord(
            id=str(uuid4()),
            job_id=offer.job_id,
            offer_id=offer.id,
            employer_id=job.employer_id,
            worker_id=offer.worker_id,
            status="accepted",
            starts_at=None,
            ended_at=None,
            completion_notes=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._bookings_by_job_id[offer.job_id] = booking
        self._bookings_by_id[booking.id] = booking
        return offer

    async def decline_offer(self, offer_id: str) -> OfferRecord:
        offer = self._offers_by_id.get(offer_id)
        if offer is None:
            raise ValueError("offer_not_found")
        if offer.status != "pending":
            raise ValueError("offer_not_pending")

        offer.status = "declined"
        offer.responded_at = datetime.now(UTC)
        return offer

    async def start_job(self, job_id: str) -> BookingRecord:
        booking = self._bookings_by_job_id.get(job_id)
        if booking is None:
            raise ValueError("booking_not_found")
        if booking.status not in {"accepted", "in_progress"}:
            raise ValueError("invalid_booking_state")

        booking.status = "in_progress"
        if booking.starts_at is None:
            booking.starts_at = datetime.now(UTC)
        booking.updated_at = datetime.now(UTC)
        return booking

    async def complete_job(self, job_id: str, completion_notes: str | None = None) -> BookingRecord:
        booking = self._bookings_by_job_id.get(job_id)
        if booking is None:
            raise ValueError("booking_not_found")
        if booking.status not in {"accepted", "in_progress"}:
            raise ValueError("invalid_booking_state")

        booking.status = "completed"
        booking.ended_at = datetime.now(UTC)
        booking.completion_notes = completion_notes
        booking.updated_at = datetime.now(UTC)
        return booking

    async def get_booking_by_id(self, booking_id: str) -> BookingRecord | None:
        return self._bookings_by_id.get(booking_id)

    async def get_booking_by_job_id(self, job_id: str) -> BookingRecord | None:
        return self._bookings_by_job_id.get(job_id)

    async def list_offers(self) -> list[OfferRecord]:
        return list(self._offers_by_id.values())

    async def list_bookings(self) -> list[BookingRecord]:
        return list(self._bookings_by_id.values())

    def reset(self) -> None:
        self._offers_by_id.clear()
        self._bookings_by_job_id.clear()
        self._bookings_by_id.clear()


offers_bookings_store = InMemoryOffersBookingsStore()
