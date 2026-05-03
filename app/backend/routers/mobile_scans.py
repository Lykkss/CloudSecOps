import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import require_role
from models.mobile_scan import MobileScan
from models.user import User
from services import mobsf_client
from services.apk_downloader import download_apk_from_playstore, extract_package_from_url

router = APIRouter(prefix="/mobile-scans", tags=["mobile"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ScanUrlRequest(BaseModel):
    url: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_mobsf(report: dict) -> dict:
    """Extrait les métriques clés du rapport JSON MobSF."""
    findings = report.get("findings", {}) or {}
    perms = report.get("permissions", {}) or {}
    trackers_data = report.get("trackers", {}) or {}

    critical = sum(1 for v in findings.values() if isinstance(v, dict) and v.get("level") == "critical")
    high     = sum(1 for v in findings.values() if isinstance(v, dict) and v.get("level") == "high")
    warning  = sum(1 for v in findings.values() if isinstance(v, dict) and v.get("level") == "warning")
    info     = sum(1 for v in findings.values() if isinstance(v, dict) and v.get("level") == "info")

    dangerous = [
        {"permission": k, "description": v.get("description", ""), "status": v.get("status", "")}
        for k, v in perms.items()
        if isinstance(v, dict) and v.get("status") == "dangerous"
    ]

    trackers = trackers_data.get("trackers", []) if isinstance(trackers_data, dict) else []

    return {
        "security_score": report.get("appsec", {}).get("security_score") if report.get("appsec") else None,
        "critical_count": critical,
        "high_count": high,
        "warning_count": warning,
        "info_count": info,
        "dangerous_perms": json.dumps(dangerous),
        "trackers": json.dumps(trackers),
        "app_name": report.get("app_name") or report.get("title"),
        "package_name": report.get("package_name") or report.get("identifier"),
        "version": report.get("version_name"),
    }


async def _run_mobsf_scan(scan: MobileScan, content: bytes, filename: str, db: Session) -> MobileScan:
    """Lance le scan MobSF et met à jour l'entrée en base."""
    upload_result = await mobsf_client.upload_apk(filename, content)
    mobsf_hash = upload_result["hash"]
    scan.mobsf_hash = mobsf_hash

    await mobsf_client.scan(mobsf_hash)

    report = await mobsf_client.report_json(mobsf_hash)
    metrics = _parse_mobsf(report)

    scan.status = "completed"
    scan.raw_json = json.dumps(report)
    scan.security_score = metrics["security_score"]
    scan.critical_count = metrics["critical_count"]
    scan.high_count = metrics["high_count"]
    scan.warning_count = metrics["warning_count"]
    scan.info_count = metrics["info_count"]
    scan.dangerous_perms = metrics["dangerous_perms"]
    scan.trackers = metrics["trackers"]
    scan.app_name = metrics["app_name"]
    scan.package_name = metrics["package_name"]
    scan.version = metrics["version"]

    db.commit()
    db.refresh(scan)
    return scan


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/scan-url",
    status_code=202,
    summary="Lancer un scan depuis une URL Play Store ou App Store",
)
async def scan_from_url(
    payload: ScanUrlRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    try:
        package_name = extract_package_from_url(payload.url)
    except ValueError as e:
        raise HTTPException(400, str(e))

    scan = MobileScan(
        file_name=f"{package_name}.apk",
        status="downloading",
        package_name=package_name,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        content, filename = await download_apk_from_playstore(payload.url)
        scan.status = "pending"
        db.commit()
        scan = await _run_mobsf_scan(scan, content, filename, db)

    except Exception as e:
        scan.status = "failed"
        db.commit()
        raise HTTPException(502, f"Erreur lors du scan : {e}")

    return _to_response(scan)


@router.post(
    "/",
    status_code=202,
    summary="Lancer un scan mobile (upload APK direct)",
)
async def upload_and_scan(
    file: UploadFile = File(..., description="Fichier APK Android"),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    if not file.filename.endswith(".apk"):
        raise HTTPException(400, "Seuls les fichiers .apk sont acceptes")

    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(413, "Fichier trop volumineux (max 200 MB)")

    scan = MobileScan(file_name=file.filename, status="pending")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        scan = await _run_mobsf_scan(scan, content, file.filename, db)
    except Exception as e:
        scan.status = "failed"
        db.commit()
        raise HTTPException(502, f"Erreur MobSF : {e}")

    return _to_response(scan)


@router.get("/", summary="Liste des scans mobiles")
def list_mobile_scans(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    return [_to_response(s) for s in
            db.query(MobileScan).order_by(MobileScan.scanned_at.desc()).all()]


@router.get("/{scan_id}", summary="Detail d'un scan mobile")
def get_mobile_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    scan = db.query(MobileScan).filter(MobileScan.id_scan == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan introuvable")
    return _to_detail(scan)


# ── Serializers ───────────────────────────────────────────────────────────────

def _to_response(s: MobileScan) -> dict:
    return {
        "id_scan": s.id_scan,
        "scanned_at": s.scanned_at,
        "app_name": s.app_name,
        "package_name": s.package_name,
        "version": s.version,
        "platform": s.platform,
        "file_name": s.file_name,
        "security_score": s.security_score,
        "critical_count": s.critical_count,
        "high_count": s.high_count,
        "warning_count": s.warning_count,
        "info_count": s.info_count,
        "status": s.status,
    }


def _to_detail(s: MobileScan) -> dict:
    d = _to_response(s)
    d["dangerous_perms"] = json.loads(s.dangerous_perms) if s.dangerous_perms else []
    d["trackers"] = json.loads(s.trackers) if s.trackers else []
    return d