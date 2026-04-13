"""Router for Jobs2Go jobs and matching v1 endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.routers.jobs2go_common import Jobs2GoModuleStatus
from app.gateway.routers.jobs2go_jobs_service import create_job_record, jobs_store, parse_job_input, rank_candidates

router = APIRouter(prefix="/v1", tags=["jobs2go-jobs-matching"])


class JobParseRequest(BaseModel):
    input_text: str = Field(min_length=3)
    location_hint: str | None = None


class JobParseResponse(BaseModel):
    title: str
    category_code: str
    skills_required: list[str]
    skill_level: str
    location_mode: str
    budget_type: str
    budget_min_cents: int
    budget_max_cents: int
    urgency: str
    confidence: float
    clarifications: list[str]


class JobCreateRequest(BaseModel):
    title: str
    description: str
    category_code: str
    location_mode: str
    skill_level: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    urgency: str | None = None
    budget_type: str | None = None
    budget_min_cents: int | None = None
    budget_max_cents: int | None = None
    currency: str = "USD"
    employer_id: str | None = None


class JobResponse(BaseModel):
    id: str
    employer_id: str
    title: str
    description: str
    category_code: str
    skill_level: str | None
    location_mode: str
    location_lat: float | None
    location_lng: float | None
    urgency: str | None
    budget_type: str | None
    budget_min_cents: int | None
    budget_max_cents: int | None
    currency: str
    created_at: datetime


class MatchCandidate(BaseModel):
    worker_id: str
    score: float
    eta_minutes: int
    price_hourly_cents: int
    why: list[str]


class MatchResponse(BaseModel):
    job_id: str
    candidates: list[MatchCandidate]


@router.get("/jobs/_status", response_model=Jobs2GoModuleStatus)
async def jobs_status() -> Jobs2GoModuleStatus:
    """Status endpoint for jobs module readiness."""
    return Jobs2GoModuleStatus(
        module="jobs",
        status="active",
        next_step="Replace in-memory jobs store with Postgres repository in Step 13",
    )


@router.post("/jobs/parse", response_model=JobParseResponse)
async def parse_job(payload: JobParseRequest) -> JobParseResponse:
    """Parse natural language input into a structured job draft."""
    parsed = parse_job_input(payload.input_text, payload.location_hint)
    return JobParseResponse(
        title=parsed["title"],
        category_code=parsed["category_code"],
        skills_required=parsed["skills_required"],
        skill_level=parsed["skill_level"],
        location_mode=parsed["location_mode"],
        budget_type=parsed["budget_type"],
        budget_min_cents=parsed["budget_min_cents"],
        budget_max_cents=parsed["budget_max_cents"],
        urgency=parsed["urgency"],
        confidence=parsed["confidence"],
        clarifications=parsed["clarifications"],
    )


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreateRequest) -> JobResponse:
    """Create a job record for matching and booking flows."""
    record = create_job_record(payload.model_dump())
    created = await jobs_store.create_job(record)
    return JobResponse(**created.__dict__)


@router.get("/jobs/{jobId}", response_model=JobResponse)
async def get_job(jobId: str) -> JobResponse:
    """Retrieve a job by ID."""
    job = await jobs_store.get_job(jobId)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job.__dict__)


@router.post("/match/jobs/{jobId}/candidates", response_model=MatchResponse)
async def match_candidates(jobId: str) -> MatchResponse:
    """Rank available workers for a specific job."""
    job = await jobs_store.get_job(jobId)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    workers = await jobs_store.list_workers()
    candidates = rank_candidates(job, workers)
    return MatchResponse(job_id=jobId, candidates=[MatchCandidate(**item) for item in candidates])


@router.get("/match/_status", response_model=Jobs2GoModuleStatus)
async def matching_status() -> Jobs2GoModuleStatus:
    """Status endpoint for matching module readiness."""
    return Jobs2GoModuleStatus(
        module="matching",
        status="active",
        next_step="Add fairness and exposure constraints in Step 13",
    )
