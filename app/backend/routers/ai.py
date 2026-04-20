import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user
from models.incident import Incident
from models.scan import ScanResult
from models.user import User
from services import ollama_client

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    context_type: str | None = None   # "scan" | "incident" | "ebios" | None
    context_id: int | None = None


@router.get("/status", summary="Statut de l'IA locale (Ollama)")
async def ai_status():
    available = await ollama_client.is_available()
    models = []
    if available:
        try:
            models = await ollama_client.list_models()
        except Exception:
            pass
    return {"available": available, "models": models}


@router.post("/chat", summary="Chat avec l'IA (streaming SSE)")
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not await ollama_client.is_available():
        raise HTTPException(503, "Ollama non disponible — vérifiez que le service est démarré")

    # Construire les messages avec system prompt + contexte optionnel
    system_content = ollama_client.SYSTEM_PROMPT

    if payload.context_type and payload.context_id:
        ctx = _load_context(db, payload.context_type, payload.context_id)
        if ctx:
            system_content += f"\n\nContexte actuel :\n{ctx}"

    messages = [{"role": "system", "content": system_content}]
    messages += [{"role": m.role, "content": m.content} for m in payload.messages]

    async def event_stream():
        try:
            async for token in ollama_client.chat_stream(messages, payload.model):
                # Format SSE
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/analyze/scan/{scan_id}", summary="Analyser un scan Trivy avec l'IA")
async def analyze_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scan = db.query(ScanResult).filter(ScanResult.id_scan == scan_id).first()
    if not scan:
        raise HTTPException(404, "Scan introuvable")

    ctx = ollama_client.build_scan_context({
        "image_name": scan.image_name, "image_tag": scan.image_tag,
        "critical_count": scan.critical_count, "high_count": scan.high_count,
        "medium_count": scan.medium_count, "low_count": scan.low_count,
        "status": scan.status,
    })
    prompt = (
        "Analyse ce scan de vulnérabilités Trivy et fournis :\n"
        "1. Une évaluation du risque global\n"
        "2. Les 3 actions prioritaires\n"
        "3. Une estimation de l'effort de remédiation\n\n"
        + ctx
    )

    messages = [
        {"role": "system", "content": ollama_client.SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    async def stream():
        async for token in ollama_client.chat_stream(messages):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/analyze/incident/{incident_id}", summary="Analyser un incident avec l'IA")
async def analyze_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    inc = db.query(Incident).filter(Incident.id_incident == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident introuvable")

    ctx = ollama_client.build_incident_context({
        "type": inc.type, "title": inc.title, "severity": inc.severity,
        "affected_resource": inc.affected_resource, "description": inc.description,
    })
    prompt = f"Analyse cet incident de sécurité et fournis :\n1. Les causes racines\n2. L'étendue probable de la compromission\n3. Les étapes de containment immédiates\n4. Les mesures préventives pour éviter la récidive\n\n{ctx}"

    messages = [
        {"role": "system", "content": ollama_client.SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    async def stream():
        async for token in ollama_client.chat_stream(messages):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _load_context(db: Session, context_type: str, context_id: int) -> str | None:
    if context_type == "scan":
        scan = db.query(ScanResult).filter(ScanResult.id_scan == context_id).first()
        if scan:
            return ollama_client.build_scan_context({
                "image_name": scan.image_name, "image_tag": scan.image_tag,
                "critical_count": scan.critical_count, "high_count": scan.high_count,
                "medium_count": scan.medium_count, "low_count": scan.low_count,
                "status": scan.status,
            })
    elif context_type == "incident":
        inc = db.query(Incident).filter(Incident.id_incident == context_id).first()
        if inc:
            return ollama_client.build_incident_context({
                "type": inc.type, "title": inc.title, "severity": inc.severity,
                "affected_resource": inc.affected_resource, "description": inc.description,
            })
    return None
