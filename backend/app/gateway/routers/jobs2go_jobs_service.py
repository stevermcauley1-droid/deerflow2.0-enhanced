"""Jobs and matching service interfaces for Jobs2Go pilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from uuid import uuid4


@dataclass
class WorkerCandidate:
    worker_id: str
    skill_tags: list[str]
    location_lat: float
    location_lng: float
    price_hourly_cents: int
    availability_now: float
    skill_match_depth: float
    reliability: float
    response_speed: float
    recent_quality: float


@dataclass
class JobRecord:
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


class InMemoryJobsStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._workers: list[WorkerCandidate] = [
            WorkerCandidate(
                worker_id="w_1",
                skill_tags=["furniture_assembly", "home_repairs"],
                location_lat=40.7128,
                location_lng=-74.0060,
                price_hourly_cents=5500,
                availability_now=0.95,
                skill_match_depth=0.90,
                reliability=0.92,
                response_speed=0.88,
                recent_quality=0.91,
            ),
            WorkerCandidate(
                worker_id="w_2",
                skill_tags=["furniture_assembly"],
                location_lat=40.7306,
                location_lng=-73.9352,
                price_hourly_cents=5000,
                availability_now=0.80,
                skill_match_depth=0.78,
                reliability=0.85,
                response_speed=0.82,
                recent_quality=0.84,
            ),
            WorkerCandidate(
                worker_id="w_3",
                skill_tags=["cleaning", "moving_help"],
                location_lat=40.6500,
                location_lng=-73.9496,
                price_hourly_cents=4200,
                availability_now=0.65,
                skill_match_depth=0.50,
                reliability=0.75,
                response_speed=0.70,
                recent_quality=0.77,
            ),
        ]

    async def create_job(self, record: JobRecord) -> JobRecord:
        self._jobs[record.id] = record
        return record

    async def get_job(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    async def list_jobs(self) -> list[JobRecord]:
        return list(self._jobs.values())

    async def list_workers(self) -> list[WorkerCandidate]:
        return self._workers

    def reset(self) -> None:
        self._jobs.clear()


def parse_job_input(input_text: str, location_hint: str | None = None) -> dict:
    lowered = input_text.lower()
    category_code = "general.task"
    skills_required = ["general_help"]

    if "ikea" in lowered or "wardrobe" in lowered or "assemble" in lowered:
        category_code = "home_services.furniture_assembly"
        skills_required = ["furniture_assembly"]
    elif "clean" in lowered:
        category_code = "home_services.cleaning"
        skills_required = ["cleaning"]

    urgency = "same_day" if any(word in lowered for word in ["today", "asap", "urgent", "now"]) else "scheduled"
    confidence = 0.9 if category_code != "general.task" else 0.68
    clarifications: list[str] = []
    if category_code == "general.task":
        clarifications.append("Please confirm the exact task category.")

    return {
        "title": _derive_title(input_text),
        "category_code": category_code,
        "skills_required": skills_required,
        "skill_level": "experienced",
        "location_mode": "onsite",
        "budget_type": "hourly",
        "budget_min_cents": 4000,
        "budget_max_cents": 7000,
        "urgency": urgency,
        "location_hint": location_hint,
        "confidence": confidence,
        "clarifications": clarifications,
    }


def create_job_record(payload: dict) -> JobRecord:
    return JobRecord(
        id=str(uuid4()),
        employer_id=payload.get("employer_id", "pilot_employer"),
        title=payload["title"],
        description=payload["description"],
        category_code=payload["category_code"],
        skill_level=payload.get("skill_level"),
        location_mode=payload["location_mode"],
        location_lat=payload.get("location_lat"),
        location_lng=payload.get("location_lng"),
        urgency=payload.get("urgency"),
        budget_type=payload.get("budget_type"),
        budget_min_cents=payload.get("budget_min_cents"),
        budget_max_cents=payload.get("budget_max_cents"),
        currency=payload.get("currency", "USD"),
        created_at=datetime.now(UTC),
    )


def rank_candidates(job: JobRecord, workers: list[WorkerCandidate]) -> list[dict]:
    ranked = []
    for worker in workers:
        skill_similarity = _skill_similarity(job.category_code, worker.skill_tags)
        distance_score = _distance_score(job.location_lat, job.location_lng, worker.location_lat, worker.location_lng)
        score = (
            0.30 * worker.availability_now
            + 0.20 * skill_similarity
            + 0.15 * distance_score
            + 0.15 * worker.reliability
            + 0.10 * worker.response_speed
            + 0.10 * worker.recent_quality
        )
        ranked.append(
            {
                "worker_id": worker.worker_id,
                "score": round(score, 4),
                "eta_minutes": int(max(8, 45 - (distance_score * 30))),
                "price_hourly_cents": worker.price_hourly_cents,
                "why": _reason_tags(worker, skill_similarity, distance_score),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def _derive_title(input_text: str) -> str:
    trimmed = input_text.strip()
    return trimmed[:90] if len(trimmed) > 90 else trimmed


def _skill_similarity(category_code: str, skill_tags: list[str]) -> float:
    if category_code.endswith("furniture_assembly") and "furniture_assembly" in skill_tags:
        return 0.95
    if category_code.endswith("cleaning") and "cleaning" in skill_tags:
        return 0.95
    text = " ".join(skill_tags)
    return max(0.35, SequenceMatcher(None, category_code, text).ratio())


def _distance_score(
    job_lat: float | None,
    job_lng: float | None,
    worker_lat: float,
    worker_lng: float,
) -> float:
    if job_lat is None or job_lng is None:
        return 0.7

    # Simple pilot approximation: Manhattan distance normalization.
    distance = abs(job_lat - worker_lat) + abs(job_lng - worker_lng)
    normalized = max(0.0, 1.0 - (distance * 6.0))
    return round(normalized, 4)


def _reason_tags(worker: WorkerCandidate, skill_similarity: float, distance_score: float) -> list[str]:
    reasons: list[str] = []
    if worker.availability_now >= 0.8:
        reasons.append("available_now")
    if skill_similarity >= 0.75:
        reasons.append("high_skill_match")
    if distance_score >= 0.65:
        reasons.append("close_by")
    if worker.response_speed >= 0.8:
        reasons.append("fast_response")
    if worker.reliability >= 0.85:
        reasons.append("reliable_history")
    return reasons


jobs_store = InMemoryJobsStore()
