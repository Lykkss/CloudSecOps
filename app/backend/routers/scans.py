import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.apikey import require_api_key
from dependencies.auth import require_role
from models.scan import ScanResult
from models.user import User
from schemas.scan import ScanDetail, ScanIngest, ScanResponse, VulnItem

router = APIRouter(prefix="/scans", tags=["scans"])

_SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}


def _parse_vulns(raw: list) -> tuple[int, int, int, int, list[VulnItem]]:
    """Extrait les compteurs et la liste depuis le JSON Trivy."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    items: list[VulnItem] = []

    for result in raw:
        for v in result.get("Vulnerabilities") or []:
            sev = v.get("Severity", "UNKNOWN").upper()
            if sev in counts:
                counts[sev] += 1
            items.append(VulnItem(
                id=v.get("VulnerabilityID", ""),
                package=v.get("PkgName", ""),
                installed_version=v.get("InstalledVersion", ""),
                fixed_version=v.get("FixedVersion"),
                severity=sev,
                title=v.get("Title"),
                description=v.get("Description"),
            ))

    items.sort(key=lambda x: _SEVERITY_ORDER.get(x.severity, 99))
    return counts["CRITICAL"], counts["HIGH"], counts["MEDIUM"], counts["LOW"], items


@router.post(
    "/",
    response_model=ScanResponse,
    status_code=201,
    summary="Ingest scan Trivy (CI)",
    description="Endpoint appelé par la CI après un scan Trivy. Authentification par clé API (`X-API-Key`).",
    tags=["scans"],
)
def ingest_scan(
    payload: ScanIngest,
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    crit, high, med, low, _ = _parse_vulns(payload.raw_json)
    status_val = "failed" if (crit > 0 or high > 0) else "passed"

    scan = ScanResult(
        image_name=payload.image_name,
        image_tag=payload.image_tag,
        git_sha=payload.git_sha,
        critical_count=crit,
        high_count=high,
        medium_count=med,
        low_count=low,
        status=status_val,
        raw_json=json.dumps(payload.raw_json),
        triggered_by=payload.triggered_by,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get(
    "/",
    response_model=list[ScanResponse],
    summary="Liste des scans",
)
def list_scans(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    return db.query(ScanResult).order_by(ScanResult.scanned_at.desc()).all()


@router.get(
    "/{scan_id}",
    response_model=ScanDetail,
    summary="Détail d'un scan avec les CVE",
)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    scan = db.query(ScanResult).filter(ScanResult.id_scan == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan introuvable")

    raw = json.loads(scan.raw_json) if scan.raw_json else []
    _, _, _, _, vulns = _parse_vulns(raw)

    return ScanDetail(
        id_scan=scan.id_scan,
        scanned_at=scan.scanned_at,
        image_name=scan.image_name,
        image_tag=scan.image_tag,
        git_sha=scan.git_sha,
        critical_count=scan.critical_count,
        high_count=scan.high_count,
        medium_count=scan.medium_count,
        low_count=scan.low_count,
        status=scan.status,
        triggered_by=scan.triggered_by,
        vulnerabilities=vulns,
    )
