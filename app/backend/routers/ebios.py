import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user, require_role
from models.ebios import EbiosAsset, EbiosFearEvent, EbiosProject, EbiosRiskSource, EbiosScenario
from models.user import User

router = APIRouter(prefix="/ebios", tags=["ebios"])


# ── Schemas inline ────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    scope: str | None = None
    context: str | None = None

class AssetCreate(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None
    critical_level: int = 2

class FearEventCreate(BaseModel):
    id_asset: int | None = None
    impact: str | None = None
    description: str | None = None
    gravity: int = 2

class RiskSourceCreate(BaseModel):
    name: str
    category: str | None = None
    motivation: str | None = None
    resources: str | None = None
    pertinence: int = 2

class ScenarioCreate(BaseModel):
    id_risk_source: int | None = None
    id_fear_event: int | None = None
    type: str = "strategic"
    title: str
    description: str | None = None
    attack_path: list[dict] | None = None
    likelihood: int = 2
    gravity: int = 2
    treatment: str = "reduce"
    measures: list[str] | None = None


# ── Projets ───────────────────────────────────────────────────────────────────

@router.get("/", summary="Liste des projets EBIOS RM")
def list_projects(db: Session = Depends(get_db), _: User = Depends(require_role("admin"))):
    return [_proj(p) for p in db.query(EbiosProject).order_by(EbiosProject.created_at.desc()).all()]


@router.post("/", status_code=201, summary="Créer un projet EBIOS RM")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db),
                   user: User = Depends(require_role("admin"))):
    p = EbiosProject(name=payload.name, scope=payload.scope,
                     context=payload.context, id_author=user.id_user)
    db.add(p); db.commit(); db.refresh(p)
    return _proj(p)


@router.get("/{project_id}", summary="Détail complet d'un projet EBIOS RM")
def get_project(project_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_role("admin"))):
    p = _get_or_404(db, EbiosProject, EbiosProject.id_project, project_id)
    assets      = db.query(EbiosAsset).filter(EbiosAsset.id_project == project_id).all()
    fear_events = db.query(EbiosFearEvent).filter(EbiosFearEvent.id_project == project_id).all()
    sources     = db.query(EbiosRiskSource).filter(EbiosRiskSource.id_project == project_id).all()
    scenarios   = db.query(EbiosScenario).filter(EbiosScenario.id_project == project_id).all()
    return {
        **_proj(p),
        "assets":      [_asset(a) for a in assets],
        "fear_events": [_fear(e) for e in fear_events],
        "risk_sources":[_source(s) for s in sources],
        "scenarios":   [_scenario(sc) for sc in scenarios],
    }


@router.patch("/{project_id}/complete", summary="Marquer un projet comme terminé")
def complete_project(project_id: int, db: Session = Depends(get_db),
                     _: User = Depends(require_role("admin"))):
    p = _get_or_404(db, EbiosProject, EbiosProject.id_project, project_id)
    p.status = "completed"; db.commit(); db.refresh(p)
    return _proj(p)


# ── Actifs ────────────────────────────────────────────────────────────────────

@router.post("/{project_id}/assets", status_code=201)
def add_asset(project_id: int, payload: AssetCreate, db: Session = Depends(get_db),
              _: User = Depends(require_role("admin"))):
    _get_or_404(db, EbiosProject, EbiosProject.id_project, project_id)
    a = EbiosAsset(id_project=project_id, **payload.model_dump())
    db.add(a); db.commit(); db.refresh(a)
    return _asset(a)


# ── Événements redoutés ───────────────────────────────────────────────────────

@router.post("/{project_id}/fear-events", status_code=201)
def add_fear_event(project_id: int, payload: FearEventCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_role("admin"))):
    _get_or_404(db, EbiosProject, EbiosProject.id_project, project_id)
    e = EbiosFearEvent(id_project=project_id, **payload.model_dump())
    db.add(e); db.commit(); db.refresh(e)
    return _fear(e)


# ── Sources de risque ─────────────────────────────────────────────────────────

@router.post("/{project_id}/risk-sources", status_code=201)
def add_risk_source(project_id: int, payload: RiskSourceCreate, db: Session = Depends(get_db),
                    _: User = Depends(require_role("admin"))):
    _get_or_404(db, EbiosProject, EbiosProject.id_project, project_id)
    s = EbiosRiskSource(id_project=project_id, **payload.model_dump())
    db.add(s); db.commit(); db.refresh(s)
    return _source(s)


# ── Scénarios ─────────────────────────────────────────────────────────────────

@router.post("/{project_id}/scenarios", status_code=201)
def add_scenario(project_id: int, payload: ScenarioCreate, db: Session = Depends(get_db),
                 _: User = Depends(require_role("admin"))):
    _get_or_404(db, EbiosProject, EbiosProject.id_project, project_id)
    data = payload.model_dump()
    data["attack_path"] = json.dumps(data["attack_path"] or [])
    data["measures"]    = json.dumps(data["measures"] or [])
    data["risk_level"]  = payload.likelihood * payload.gravity
    sc = EbiosScenario(id_project=project_id, **data)
    db.add(sc); db.commit(); db.refresh(sc)
    return _scenario(sc)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db, model, pk_col, pk_val):
    obj = db.query(model).filter(pk_col == pk_val).first()
    if not obj:
        raise HTTPException(404, f"{model.__name__} introuvable")
    return obj

def _proj(p): return {"id_project": p.id_project, "created_at": p.created_at, "name": p.name,
                       "scope": p.scope, "context": p.context, "status": p.status}
def _asset(a): return {"id_asset": a.id_asset, "id_project": a.id_project, "name": a.name,
                        "type": a.type, "description": a.description, "critical_level": a.critical_level}
def _fear(e): return {"id_event": e.id_event, "id_project": e.id_project, "id_asset": e.id_asset,
                       "impact": e.impact, "description": e.description, "gravity": e.gravity}
def _source(s): return {"id_source": s.id_source, "id_project": s.id_project, "name": s.name,
                         "category": s.category, "motivation": s.motivation,
                         "resources": s.resources, "pertinence": s.pertinence}
def _scenario(sc): return {
    "id_scenario": sc.id_scenario, "id_project": sc.id_project,
    "id_risk_source": sc.id_risk_source, "id_fear_event": sc.id_fear_event,
    "type": sc.type, "title": sc.title, "description": sc.description,
    "attack_path": json.loads(sc.attack_path) if sc.attack_path else [],
    "likelihood": sc.likelihood, "gravity": sc.gravity, "risk_level": sc.risk_level,
    "treatment": sc.treatment,
    "measures": json.loads(sc.measures) if sc.measures else [],
}
