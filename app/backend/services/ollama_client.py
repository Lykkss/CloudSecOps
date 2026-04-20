"""Client pour l'API Ollama (IA locale)."""
import json
from typing import AsyncIterator

import httpx

from core.config import settings


async def is_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.OLLAMA_URL}/api/version")
            return r.status_code == 200
    except Exception:
        return False


async def list_models() -> list[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{settings.OLLAMA_URL}/api/tags")
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]


async def chat_stream(
    messages: list[dict],
    model: str | None = None,
) -> AsyncIterator[str]:
    """
    Génère une réponse en streaming.
    Chaque chunk est une chaîne de caractères à envoyer au client via SSE.
    """
    payload = {
        "model": model or settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream(
            "POST",
            f"{settings.OLLAMA_URL}/api/chat",
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


SYSTEM_PROMPT = """Tu es un expert en cybersécurité cloud (AWS, Terraform, DevSecOps).
Tu analyses des rapports de sécurité, des scans de vulnérabilités et des incidents.
Réponds en français, de manière concise et structurée.
Utilise des emojis pour les niveaux de sévérité : 🔴 Critique, 🟠 Élevé, 🟡 Moyen, 🟢 Faible.
"""

def build_scan_context(scan: dict) -> str:
    return f"""Voici un rapport de scan Trivy à analyser :
Image : {scan.get('image_name')}:{scan.get('image_tag')}
Vulnérabilités : {scan.get('critical_count')} CRITICAL, {scan.get('high_count')} HIGH, {scan.get('medium_count')} MEDIUM, {scan.get('low_count')} LOW
Statut : {scan.get('status')}
"""

def build_incident_context(incident: dict) -> str:
    return f"""Voici un incident de sécurité à analyser :
Type : {incident.get('type')}
Titre : {incident.get('title')}
Sévérité : {incident.get('severity')}
Ressource affectée : {incident.get('affected_resource')}
Description : {incident.get('description')}
"""

def build_ebios_context(project: dict) -> str:
    return f"""Voici un projet EBIOS RM à analyser :
Nom : {project.get('name')}
Périmètre : {project.get('scope')}
Contexte : {project.get('context')}
"""
