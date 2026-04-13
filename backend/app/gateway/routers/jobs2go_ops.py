"""Ops and KPI endpoints for Jobs2Go pilot monitoring."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.gateway.routers.jobs2go_chat_reviews_trust_service import chat_reviews_trust_store
from app.gateway.routers.jobs2go_jobs_service import jobs_store
from app.gateway.routers.jobs2go_offers_service import offers_bookings_store
from app.gateway.routers.jobs2go_payments_service import payments_store

router = APIRouter(prefix="/v1/ops", tags=["jobs2go-ops"])


class ModuleHealth(BaseModel):
    name: str
    status: str
    note: str


class OpsModulesResponse(BaseModel):
    modules: list[ModuleHealth]


class OpsKpiResponse(BaseModel):
    jobs_created: int
    offers_sent: int
    offers_accepted: int
    bookings_completed: int
    fill_rate_15_min_pct: float
    completion_rate_pct: float
    escrow_authorized_count: int
    escrow_released_count: int
    escrow_release_rate_pct: float
    reviews_count: int
    trust_reports_count: int
    trust_priority_reports_count: int


@router.get("/modules", response_model=OpsModulesResponse)
async def get_module_health() -> OpsModulesResponse:
    """Return module health summary for pilot operations."""
    modules = [
        ModuleHealth(name="auth_kyc", status="active", note="Registration, login, and KYC start enabled"),
        ModuleHealth(name="jobs_matching", status="active", note="Parse, create, and ranking endpoints enabled"),
        ModuleHealth(name="offers_bookings", status="active", note="Offer lifecycle and job transitions enabled"),
        ModuleHealth(name="payments_escrow", status="active", note="Escrow authorize/release with ledger checks"),
        ModuleHealth(name="chat_reviews_trust", status="active", note="Messaging, reviews, and trust reports enabled"),
    ]
    return OpsModulesResponse(modules=modules)


@router.get("/kpi", response_model=OpsKpiResponse)
async def get_kpi_snapshot() -> OpsKpiResponse:
    """Return pilot KPI snapshot aggregated from in-memory service state."""
    jobs = await jobs_store.list_jobs()
    offers = await offers_bookings_store.list_offers()
    bookings = await offers_bookings_store.list_bookings()
    payments = await payments_store.list_payments()
    reviews = await chat_reviews_trust_store.list_reviews()
    reports = await chat_reviews_trust_store.list_reports()

    jobs_created = len(jobs)
    offers_sent = len(offers)
    offers_accepted = sum(1 for item in offers if item.status == "accepted")
    bookings_completed = sum(1 for item in bookings if item.status == "completed")

    escrow_authorized_count = sum(1 for item in payments if item.escrow_status in {"authorized", "released"})
    escrow_released_count = sum(1 for item in payments if item.escrow_status == "released")

    fill_rate_15_min_pct = round((offers_accepted / jobs_created) * 100, 2) if jobs_created else 0.0
    completion_rate_pct = round((bookings_completed / offers_accepted) * 100, 2) if offers_accepted else 0.0
    escrow_release_rate_pct = (
        round((escrow_released_count / escrow_authorized_count) * 100, 2) if escrow_authorized_count else 0.0
    )
    trust_priority_reports_count = sum(1 for item in reports if item.status == "priority")

    return OpsKpiResponse(
        jobs_created=jobs_created,
        offers_sent=offers_sent,
        offers_accepted=offers_accepted,
        bookings_completed=bookings_completed,
        fill_rate_15_min_pct=fill_rate_15_min_pct,
        completion_rate_pct=completion_rate_pct,
        escrow_authorized_count=escrow_authorized_count,
        escrow_released_count=escrow_released_count,
        escrow_release_rate_pct=escrow_release_rate_pct,
        reviews_count=len(reviews),
        trust_reports_count=len(reports),
        trust_priority_reports_count=trust_priority_reports_count,
    )
