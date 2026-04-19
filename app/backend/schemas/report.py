from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FindingItem(BaseModel):
    title: str
    severity: str
    description: str
    evidence: str | None = None


class RecommendationItem(BaseModel):
    priority: str   # "immediate" | "short_term" | "long_term"
    action: str
    owner: str | None = None


class ReportCreate(BaseModel):
    title: str
    id_incident: int | None = None
    executive_summary: str
    findings: list[FindingItem]
    recommendations: list[RecommendationItem]
    status: str = "draft"


class ReportResponse(BaseModel):
    id_report: int
    created_at: datetime
    title: str
    status: str
    id_incident: int | None
    executive_summary: str
    findings: list[Any] | None = None
    recommendations: list[Any] | None = None
    id_author: int | None

    class Config:
        from_attributes = True
