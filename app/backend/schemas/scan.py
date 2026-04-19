from datetime import datetime
from typing import Any

from pydantic import BaseModel


class VulnItem(BaseModel):
    id: str
    package: str
    installed_version: str
    fixed_version: str | None
    severity: str
    title: str | None = None
    description: str | None = None


class ScanIngest(BaseModel):
    """Payload posté par la CI après un scan Trivy."""
    image_name: str
    image_tag: str
    git_sha: str | None = None
    triggered_by: str = "ci"
    # JSON brut complet de Trivy (Results[])
    raw_json: list[Any]


class ScanResponse(BaseModel):
    id_scan: int
    scanned_at: datetime
    image_name: str
    image_tag: str
    git_sha: str | None
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    status: str
    triggered_by: str

    class Config:
        from_attributes = True


class ScanDetail(ScanResponse):
    vulnerabilities: list[VulnItem] = []
