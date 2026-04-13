"""Scaffold router for Jobs2Go worker profile domain."""

from fastapi import APIRouter

from app.gateway.routers.jobs2go_common import Jobs2GoModuleStatus

router = APIRouter(prefix="/v1/workers", tags=["jobs2go-workers"])


@router.get("/_status", response_model=Jobs2GoModuleStatus)
async def workers_status() -> Jobs2GoModuleStatus:
    """Scaffold readiness for workers endpoints."""
    return Jobs2GoModuleStatus(
        module="workers",
        status="scaffold_ready",
        next_step="Implement profile, skills, and availability endpoints in Step 6",
    )
