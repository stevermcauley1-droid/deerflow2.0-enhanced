"""Router for Jobs2Go payments and escrow endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.routers.jobs2go_common import Jobs2GoModuleStatus
from app.gateway.routers.jobs2go_payments_service import payments_store

router = APIRouter(prefix="/v1/payments", tags=["jobs2go-payments"])


class EscrowAuthorizeRequest(BaseModel):
    booking_id: str
    payment_method_id: str
    amount_cents: int = Field(gt=0)
    currency: str = "USD"


class EscrowReleaseRequest(BaseModel):
    booking_id: str


class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    employer_id: str
    worker_id: str
    escrow_status: str
    gross_amount_cents: int
    platform_fee_cents: int
    worker_payout_cents: int
    currency: str
    created_at: datetime
    updated_at: datetime


@router.get("/_status", response_model=Jobs2GoModuleStatus)
async def payments_status() -> Jobs2GoModuleStatus:
    """Status endpoint for payments module readiness."""
    return Jobs2GoModuleStatus(
        module="payments",
        status="active",
        next_step="Wire provider webhooks and persistence in Step 13",
    )


@router.post("/escrow/authorize", response_model=PaymentResponse)
async def escrow_authorize(payload: EscrowAuthorizeRequest) -> PaymentResponse:
    """Authorize escrow hold and create balanced ledger entries."""
    try:
        payment = await payments_store.authorize_escrow(
            booking_id=payload.booking_id,
            payment_method_id=payload.payment_method_id,
            amount_cents=payload.amount_cents,
            currency=payload.currency,
        )
    except ValueError as exc:
        if str(exc) == "booking_not_found":
            raise HTTPException(status_code=404, detail="Booking not found") from exc
        if str(exc) == "payment_already_exists":
            raise HTTPException(status_code=409, detail="Escrow already authorized for booking") from exc
        if str(exc) == "invalid_amount":
            raise HTTPException(status_code=400, detail="Invalid amount") from exc
        if str(exc) == "ledger_unbalanced":
            raise HTTPException(status_code=500, detail="Ledger invariant failed") from exc
        raise

    return PaymentResponse(**payment.__dict__)


@router.post("/escrow/release", response_model=PaymentResponse)
async def escrow_release(payload: EscrowReleaseRequest) -> PaymentResponse:
    """Release escrow after job completion with balanced settlement entries."""
    try:
        payment = await payments_store.release_escrow(booking_id=payload.booking_id)
    except ValueError as exc:
        if str(exc) == "booking_not_found":
            raise HTTPException(status_code=404, detail="Booking not found") from exc
        if str(exc) == "payment_not_found":
            raise HTTPException(status_code=404, detail="Payment not found") from exc
        if str(exc) == "invalid_payment_state":
            raise HTTPException(status_code=409, detail="Payment is not in releasable state") from exc
        if str(exc) == "booking_not_completed":
            raise HTTPException(status_code=409, detail="Booking must be completed before release") from exc
        if str(exc) == "ledger_unbalanced":
            raise HTTPException(status_code=500, detail="Ledger invariant failed") from exc
        raise

    return PaymentResponse(**payment.__dict__)


@router.get("/{paymentId}", response_model=PaymentResponse)
async def get_payment(paymentId: str) -> PaymentResponse:
    """Fetch payment details by payment ID."""
    payment = await payments_store.get_payment(paymentId)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse(**payment.__dict__)
