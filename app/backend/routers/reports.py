import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user, require_role
from models.report import ForensicReport
from models.user import User
from schemas.report import ReportCreate, ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/", response_model=list[ReportResponse], summary="Liste des rapports forensiques")
def list_reports(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    rows = db.query(ForensicReport).order_by(ForensicReport.created_at.desc()).all()
    return [_to_response(r) for r in rows]


@router.get("/{report_id}", response_model=ReportResponse, summary="Détail d'un rapport")
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    r = db.query(ForensicReport).filter(ForensicReport.id_report == report_id).first()
    if not r:
        raise HTTPException(404, "Rapport introuvable")
    return _to_response(r)


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=201,
    summary="Créer un rapport forensique",
)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    r = ForensicReport(
        title=payload.title,
        status=payload.status,
        id_incident=payload.id_incident,
        executive_summary=payload.executive_summary,
        findings=json.dumps([f.model_dump() for f in payload.findings]),
        recommendations=json.dumps([rec.model_dump() for rec in payload.recommendations]),
        id_author=current_user.id_user,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _to_response(r)


@router.patch(
    "/{report_id}/finalize",
    response_model=ReportResponse,
    summary="Finaliser un rapport (draft → final)",
)
def finalize_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    r = db.query(ForensicReport).filter(ForensicReport.id_report == report_id).first()
    if not r:
        raise HTTPException(404, "Rapport introuvable")
    r.status = "final"
    db.commit()
    db.refresh(r)
    return _to_response(r)


def _to_response(r: ForensicReport) -> ReportResponse:
    return ReportResponse(
        id_report=r.id_report,
        created_at=r.created_at,
        title=r.title,
        status=r.status,
        id_incident=r.id_incident,
        executive_summary=r.executive_summary,
        findings=json.loads(r.findings) if r.findings else [],
        recommendations=json.loads(r.recommendations) if r.recommendations else [],
        id_author=r.id_author,
    )
