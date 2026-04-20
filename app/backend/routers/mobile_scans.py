import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import require_role
from models.mobile_scan import MobileScan
from models.user import User
from services import mobsf_client

router = APIRouter(prefix="/mobile-scans", tags=["mobile"])


def _parse_mobsf(report: dict) -> dict:
    """Extrait les métriques clés du rapport JSON MobSF."""
    vuln = report.get("android_api", {}) or {}
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


@router.post(
    "/",
    status_code=202,
    summary="Lancer un scan mobile (upload APK)",
)
async def upload_and_scan(
    file: UploadFile = File(..., description="Fichier APK Android"),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    if not file.filename.endswith(".apk"):
        raise HTTPException(400, "Seuls les fichiers .apk sont acceptés")

    content = await file.read()
    if len(content) > 200 * 1024 * 1024:  # 200 MB max
        raise HTTPException(413, "Fichier trop volumineux (max 200 MB)")

    # Créer une entrée pending
    scan = MobileScan(file_name=file.filename, status="pending")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        # Upload vers MobSF
        upload_result = await mobsf_client.upload_apk(file.filename, content)
        mobsf_hash = upload_result["hash"]
        scan.mobsf_hash = mobsf_hash

        # Scan
        await mobsf_client.scan(mobsf_hash)

        # Rapport JSON
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

    except Exception as e:
        scan.status = "failed"
        db.commit()
        raise HTTPException(502, f"Erreur MobSF : {e}")

    db.commit()
    db.refresh(scan)
    return _to_response(scan)


@router.get("/", summary="Liste des scans mobiles")
def list_mobile_scans(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    return [_to_response(s) for s in
            db.query(MobileScan).order_by(MobileScan.scanned_at.desc()).all()]


@router.get("/{scan_id}", summary="Détail d'un scan mobile")
def get_mobile_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    scan = db.query(MobileScan).filter(MobileScan.id_scan == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan introuvable")
    return _to_detail(scan)


def _to_response(s: MobileScan) -> dict:
    return {
        "id_scan": s.id_scan, "scanned_at": s.scanned_at,
        "app_name": s.app_name, "package_name": s.package_name,
        "version": s.version, "platform": s.platform,
        "file_name": s.file_name, "security_score": s.security_score,
        "critical_count": s.critical_count, "high_count": s.high_count,
        "warning_count": s.warning_count, "info_count": s.info_count,
        "status": s.status,
    }


def _to_detail(s: MobileScan) -> dict:
    d = _to_response(s)
    d["dangerous_perms"] = json.loads(s.dangerous_perms) if s.dangerous_perms else []
    d["trackers"] = json.loads(s.trackers) if s.trackers else []
    return d
