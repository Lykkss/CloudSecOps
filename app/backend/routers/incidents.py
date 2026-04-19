import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user, require_role
from models.incident import Incident
from models.user import User
from schemas.incident import IncidentResponse, StatusUpdate

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dt(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)).isoformat()


# ── Simulation IAM compromise ─────────────────────────────────────────────────

def _generate_iam_simulation(user: User) -> dict:
    """Génère un scénario réaliste de compromission IAM."""
    timeline = [
        {"ts": _dt(120), "event": "Credential exposure",
         "detail": "Clé d'accès AWS (AKIA…) détectée dans un dépôt GitHub public"},
        {"ts": _dt(110), "event": "First API call from unusual IP",
         "detail": "GetCallerIdentity depuis 185.220.101.42 (Tor exit node, DE)"},
        {"ts": _dt(105), "event": "IAM enumeration",
         "detail": "ListUsers, ListRoles, ListPolicies — 47 appels en 3 minutes"},
        {"ts": _dt(95),  "event": "Privilege escalation attempt",
         "detail": "AttachUserPolicy : tentative d'attachement de AdministratorAccess"},
        {"ts": _dt(90),  "event": "CloudTrail tampering",
         "detail": "StopLogging sur le trail principal — journalisation coupée"},
        {"ts": _dt(85),  "event": "S3 exfiltration",
         "detail": "GetObject sur s3://cloud-secops-logs-dev — 1 247 objets téléchargés"},
        {"ts": _dt(70),  "event": "New backdoor user created",
         "detail": "CreateUser: svc-backup-tmp / CreateAccessKey émis"},
        {"ts": _dt(60),  "event": "Lateral movement",
         "detail": "AssumeRole vers le rôle cloud-secops-ec2-role depuis l'utilisateur compromis"},
        {"ts": _dt(30),  "event": "Detection — CloudWatch alarm",
         "detail": "Alarme UnauthorizedAPICalls déclenchée après 12 erreurs AccessDenied"},
        {"ts": _dt(0),   "event": "Incident déclaré",
         "detail": f"Incident ouvert par {user.email} — containment initié"},
    ]

    ioc = [
        {"type": "IP",          "value": "185.220.101.42", "context": "Tor exit node — source des appels API"},
        {"type": "IAM_USER",    "value": "svc-backup-tmp",  "context": "Utilisateur backdoor créé par l'attaquant"},
        {"type": "ACCESS_KEY",  "value": "AKIAIOSFODNN7EXAMPLE", "context": "Clé exposée sur GitHub"},
        {"type": "S3_PREFIX",   "value": "s3://cloud-secops-logs-dev/", "context": "Bucket exfiltré"},
        {"type": "API_CALL",    "value": "StopLogging",     "context": "Anti-forensic — trail désactivé"},
        {"type": "USER_AGENT",  "value": "aws-cli/2.13.0 Python/3.11 Linux/5.15", "context": "UA de l'attaquant"},
    ]

    return {
        "type": "iam_compromise",
        "title": "Compromission de clé d'accès IAM — exfiltration S3",
        "severity": "critical",
        "status": "open",
        "affected_resource": "iam::user/cloudsecops-ci + s3://cloud-secops-logs-dev",
        "description": (
            "Une clé d'accès AWS a été exposée dans un dépôt GitHub public. "
            "L'attaquant a procédé à une énumération IAM, tenté une élévation de privilèges, "
            "désactivé CloudTrail, exfiltré des objets S3 et créé un utilisateur backdoor "
            "avant d'être détecté par une alarme CloudWatch."
        ),
        "timeline": json.dumps(timeline),
        "ioc": json.dumps(ioc),
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[IncidentResponse], summary="Liste des incidents")
def list_incidents(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    rows = db.query(Incident).order_by(Incident.created_at.desc()).all()
    return [_to_response(i) for i in rows]


@router.get("/{incident_id}", response_model=IncidentResponse, summary="Détail d'un incident")
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    inc = db.query(Incident).filter(Incident.id_incident == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident introuvable")
    return _to_response(inc)


@router.post(
    "/simulate/iam",
    response_model=IncidentResponse,
    status_code=201,
    summary="Simuler une compromission IAM",
    description="Génère un scénario réaliste de compromission de clé IAM et l'enregistre comme incident.",
)
def simulate_iam(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    data = _generate_iam_simulation(current_user)
    inc = Incident(**data, id_user=current_user.id_user)
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return _to_response(inc)


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentResponse,
    summary="Mettre à jour le statut d'un incident",
)
def update_status(
    incident_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    allowed = {"open", "investigating", "resolved"}
    if payload.status not in allowed:
        raise HTTPException(400, f"Statut invalide. Valeurs : {allowed}")

    inc = db.query(Incident).filter(Incident.id_incident == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident introuvable")

    inc.status = payload.status
    db.commit()
    db.refresh(inc)
    return _to_response(inc)


def _to_response(inc: Incident) -> IncidentResponse:
    return IncidentResponse(
        id_incident=inc.id_incident,
        created_at=inc.created_at,
        type=inc.type,
        title=inc.title,
        severity=inc.severity,
        status=inc.status,
        affected_resource=inc.affected_resource,
        description=inc.description,
        timeline=json.loads(inc.timeline) if inc.timeline else None,
        ioc=json.loads(inc.ioc) if inc.ioc else None,
    )
