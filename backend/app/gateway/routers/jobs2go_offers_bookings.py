"""Router for Jobs2Go offers and bookings lifecycle endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.routers.jobs2go_common import Jobs2GoModuleStatus
from app.gateway.routers.jobs2go_offers_service import offers_bookings_store

router = APIRouter(prefix="/v1", tags=["jobs2go-offers-bookings"])


class CreateOfferRequest(BaseModel):
    worker_id: str
    message: str | None = None
    proposed_amount_cents: int = Field(ge=0)
    currency: str = "USD"
    expires_at: datetime | None = None


class OfferResponse(BaseModel):
    id: str
    job_id: str
    worker_id: str
    status: str
    message: str | None = None
    proposed_amount_cents: int
    currency: str
    expires_at: datetime | None = None
    responded_at: datetime | None = None
    created_at: datetime


class BookingStateResponse(BaseModel):
    booking_id: str
    job_id: str
    offer_id: str
    status: str
    starts_at: datetime | None = None
    ended_at: datetime | None = None
    completion_notes: str | None = None
    updated_at: datetime


class CompleteJobRequest(BaseModel):
    completion_notes: str | None = None


@router.get("/offers/_status", response_model=Jobs2GoModuleStatus)
async def offers_status() -> Jobs2GoModuleStatus:
    """Status endpoint for offers module readiness."""
    return Jobs2GoModuleStatus(
        module="offers",
        status="active",
        next_step="Add offer expiry worker in Step 13",
    )


@router.post("/jobs/{jobId}/offers", response_model=OfferResponse, status_code=201)
async def create_offer(jobId: str, payload: CreateOfferRequest) -> OfferResponse:
    """Create a new offer for a worker on a specific job."""
    try:
        offer = await offers_bookings_store.create_offer(
            job_id=jobId,
            worker_id=payload.worker_id,
            message=payload.message,
            proposed_amount_cents=payload.proposed_amount_cents,
            currency=payload.currency,
            expires_at=payload.expires_at,
        )
    except ValueError as exc:
        if str(exc) == "job_not_found":
            raise HTTPException(status_code=404, detail="Job not found") from exc
        if str(exc) == "invalid_amount":
            raise HTTPException(status_code=400, detail="Invalid proposed amount") from exc
        raise

    return OfferResponse(**offer.__dict__)


@router.post("/offers/{offerId}/accept", response_model=OfferResponse)
async def accept_offer(offerId: str) -> OfferResponse:
    """Accept an existing offer and open a booking."""
    try:
        offer = await offers_bookings_store.accept_offer(offerId)
    except ValueError as exc:
        if str(exc) == "offer_not_found":
            raise HTTPException(status_code=404, detail="Offer not found") from exc
        if str(exc) == "offer_not_pending":
            raise HTTPException(status_code=409, detail="Offer is not pending") from exc
        raise
    return OfferResponse(**offer.__dict__)


@router.post("/offers/{offerId}/decline", response_model=OfferResponse)
async def decline_offer(offerId: str) -> OfferResponse:
    """Decline an existing offer."""
    try:
        offer = await offers_bookings_store.decline_offer(offerId)
    except ValueError as exc:
        if str(exc) == "offer_not_found":
            raise HTTPException(status_code=404, detail="Offer not found") from exc
        if str(exc) == "offer_not_pending":
            raise HTTPException(status_code=409, detail="Offer is not pending") from exc
        raise
    return OfferResponse(**offer.__dict__)


@router.post("/jobs/{jobId}/start", response_model=BookingStateResponse)
async def start_job(jobId: str) -> BookingStateResponse:
    """Move booking to in progress state for the target job."""
    try:
        booking = await offers_bookings_store.start_job(jobId)
    except ValueError as exc:
        if str(exc) == "booking_not_found":
            raise HTTPException(status_code=404, detail="Booking not found") from exc
        if str(exc) == "invalid_booking_state":
            raise HTTPException(status_code=409, detail="Booking state does not allow start") from exc
        raise

    return BookingStateResponse(
        booking_id=booking.id,
        job_id=booking.job_id,
        offer_id=booking.offer_id,
        status=booking.status,
        starts_at=booking.starts_at,
        ended_at=booking.ended_at,
        completion_notes=booking.completion_notes,
        updated_at=booking.updated_at,
    )


@router.post("/jobs/{jobId}/complete", response_model=BookingStateResponse)
async def complete_job(jobId: str, payload: CompleteJobRequest) -> BookingStateResponse:
    """Complete booking for a job and capture completion notes."""
    try:
        booking = await offers_bookings_store.complete_job(jobId, payload.completion_notes)
    except ValueError as exc:
        if str(exc) == "booking_not_found":
            raise HTTPException(status_code=404, detail="Booking not found") from exc
        if str(exc) == "invalid_booking_state":
            raise HTTPException(status_code=409, detail="Booking state does not allow completion") from exc
        raise

    return BookingStateResponse(
        booking_id=booking.id,
        job_id=booking.job_id,
        offer_id=booking.offer_id,
        status=booking.status,
        starts_at=booking.starts_at,
        ended_at=booking.ended_at,
        completion_notes=booking.completion_notes,
        updated_at=booking.updated_at,
    )


@router.get("/jobs/{jobId}/booking", response_model=BookingStateResponse)
async def get_booking_for_job(jobId: str) -> BookingStateResponse:
    """Fetch booking state by job ID."""
    booking = await offers_bookings_store.get_booking_by_job_id(jobId)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    return BookingStateResponse(
        booking_id=booking.id,
        job_id=booking.job_id,
        offer_id=booking.offer_id,
        status=booking.status,
        starts_at=booking.starts_at,
        ended_at=booking.ended_at,
        completion_notes=booking.completion_notes,
        updated_at=booking.updated_at,
    )


@router.get("/bookings/_status", response_model=Jobs2GoModuleStatus)
async def bookings_status() -> Jobs2GoModuleStatus:
    """Status endpoint for bookings module readiness."""
    return Jobs2GoModuleStatus(
        module="bookings",
        status="active",
        next_step="Add cancellation and dispute transitions in Step 10",
    )
