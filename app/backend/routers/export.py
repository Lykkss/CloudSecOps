import json
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import require_role
from models.ebios import EbiosAsset, EbiosFearEvent, EbiosProject, EbiosRiskSource, EbiosScenario
from models.incident import Incident
from models.mobile_scan import MobileScan
from models.report import ForensicReport
from models.scan import ScanResult
from models.user import User
from routers.scans import _parse_vulns
from services import pdf_generator

router = APIRouter(prefix="/export", tags=["export"])

_PDF_HEADERS = {"Content-Disposition": "attachment"}


def _pdf_response(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf/scan/{scan_id}", summary="Export PDF — Scan Trivy")
def export_scan(scan_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))):
    scan = db.query(ScanResult).filter(ScanResult.id_scan == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan introuvable")

    raw = json.loads(scan.raw_json) if scan.raw_json else []
    _, _, _, _, vulns = _parse_vulns(raw)

    scan_dict = {
        "id_scan": scan.id_scan, "image_name": scan.image_name, "image_tag": scan.image_tag,
        "git_sha": scan.git_sha, "critical_count": scan.critical_count,
        "high_count": scan.high_count, "medium_count": scan.medium_count,
        "low_count": scan.low_count, "status": scan.status,
        "triggered_by": scan.triggered_by,
        "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else "",
    }
    pdf = pdf_generator.scan_pdf(scan_dict, [v.model_dump() for v in vulns])
    return _pdf_response(pdf, f"trivy-scan-{scan_id}.pdf")


@router.get("/pdf/mobile-scan/{scan_id}", summary="Export PDF — Scan Mobile MobSF")
def export_mobile_scan(scan_id: int, db: Session = Depends(get_db),
                       _: User = Depends(require_role("admin"))):
    scan = db.query(MobileScan).filter(MobileScan.id_scan == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan introuvable")

    scan_dict = {
        "id_scan": scan.id_scan, "app_name": scan.app_name,
        "package_name": scan.package_name, "version": scan.version,
        "platform": scan.platform, "file_name": scan.file_name,
        "security_score": scan.security_score, "critical_count": scan.critical_count,
        "high_count": scan.high_count, "warning_count": scan.warning_count,
        "info_count": scan.info_count, "status": scan.status,
        "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else "",
        "dangerous_perms": json.loads(scan.dangerous_perms) if scan.dangerous_perms else [],
        "trackers": json.loads(scan.trackers) if scan.trackers else [],
    }
    pdf = pdf_generator.mobile_scan_pdf(scan_dict)
    return _pdf_response(pdf, f"mobile-scan-{scan_id}.pdf")


@router.get("/pdf/incident/{incident_id}", summary="Export PDF — Rapport d'incident")
def export_incident(incident_id: int, db: Session = Depends(get_db),
                    _: User = Depends(require_role("admin"))):
    inc = db.query(Incident).filter(Incident.id_incident == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident introuvable")

    inc_dict = {
        "id_incident": inc.id_incident, "type": inc.type, "title": inc.title,
        "severity": inc.severity, "status": inc.status,
        "affected_resource": inc.affected_resource, "description": inc.description,
        "created_at": inc.created_at.isoformat() if inc.created_at else "",
        "timeline": json.loads(inc.timeline) if inc.timeline else [],
        "ioc": json.loads(inc.ioc) if inc.ioc else [],
    }
    pdf = pdf_generator.incident_pdf(inc_dict)
    return _pdf_response(pdf, f"incident-{incident_id}.pdf")


@router.get("/pdf/report/{report_id}", summary="Export PDF — Rapport forensique")
def export_report(report_id: int, db: Session = Depends(get_db),
                  _: User = Depends(require_role("admin"))):
    r = db.query(ForensicReport).filter(ForensicReport.id_report == report_id).first()
    if not r:
        raise HTTPException(404, "Rapport introuvable")

    r_dict = {
        "id_report": r.id_report, "title": r.title, "status": r.status,
        "id_incident": r.id_incident, "id_author": r.id_author,
        "executive_summary": r.executive_summary,
        "created_at": r.created_at.isoformat() if r.created_at else "",
        "findings": json.loads(r.findings) if r.findings else [],
        "recommendations": json.loads(r.recommendations) if r.recommendations else [],
    }
    pdf = pdf_generator.forensic_report_pdf(r_dict)
    return _pdf_response(pdf, f"forensic-report-{report_id}.pdf")


@router.get("/pdf/ebios/{project_id}", summary="Export PDF — Analyse EBIOS RM")
def export_ebios(project_id: int, db: Session = Depends(get_db),
                 _: User = Depends(require_role("admin"))):
    p = db.query(EbiosProject).filter(EbiosProject.id_project == project_id).first()
    if not p:
        raise HTTPException(404, "Projet EBIOS introuvable")

    from routers.ebios import _asset, _fear, _proj, _scenario, _source
    proj_dict = _proj(p)
    proj_dict["created_at"] = p.created_at.isoformat() if p.created_at else ""

    assets    = [_asset(a) for a in db.query(EbiosAsset).filter(EbiosAsset.id_project == project_id).all()]
    fears     = [_fear(e) for e in db.query(EbiosFearEvent).filter(EbiosFearEvent.id_project == project_id).all()]
    sources   = [_source(s) for s in db.query(EbiosRiskSource).filter(EbiosRiskSource.id_project == project_id).all()]
    scenarios = [_scenario(sc) for sc in db.query(EbiosScenario).filter(EbiosScenario.id_project == project_id).all()]

    pdf = pdf_generator.ebios_pdf(proj_dict, assets, fears, sources, scenarios)
    return _pdf_response(pdf, f"ebios-{project_id}.pdf")
