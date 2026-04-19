from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    ts: str          # ISO datetime
    event: str
    detail: str | None = None


class IncidentResponse(BaseModel):
    id_incident: int
    created_at: datetime
    type: str
    title: str
    severity: str
    status: str
    affected_resource: str | None
    description: str | None
    timeline: list[Any] | None = None
    ioc: list[Any] | None = None

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str  # "open" | "investigating" | "resolved"
