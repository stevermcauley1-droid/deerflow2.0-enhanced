"""Shared scaffold models for Jobs2Go gateway modules."""

from pydantic import BaseModel


class Jobs2GoModuleStatus(BaseModel):
    module: str
    status: str
    next_step: str
