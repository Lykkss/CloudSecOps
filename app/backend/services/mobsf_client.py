"""Client HTTP pour l'API REST de MobSF."""
import httpx

from core.config import settings


def _headers() -> dict:
    return {"Authorization": settings.MOBSF_API_KEY}


async def upload_apk(filename: str, content: bytes) -> dict:
    """Envoie un APK à MobSF — retourne {hash, scan_type, file_name, …}."""
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{settings.MOBSF_URL}/api/v1/upload",
            headers=_headers(),
            files={"file": (filename, content, "application/octet-stream")},
        )
        r.raise_for_status()
        return r.json()


async def scan(mobsf_hash: str, rescan: bool = False) -> dict:
    """Lance l'analyse d'un fichier déjà uploadé."""
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            f"{settings.MOBSF_URL}/api/v1/scan",
            headers=_headers(),
            data={"hash": mobsf_hash, "re_scan": "1" if rescan else "0"},
        )
        r.raise_for_status()
        return r.json()


async def report_json(mobsf_hash: str) -> dict:
    """Récupère le rapport JSON complet."""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{settings.MOBSF_URL}/api/v1/report_json",
            headers=_headers(),
            data={"hash": mobsf_hash},
        )
        r.raise_for_status()
        return r.json()


async def report_pdf(mobsf_hash: str) -> bytes:
    """Récupère le rapport PDF généré par MobSF."""
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{settings.MOBSF_URL}/api/v1/download_pdf",
            headers=_headers(),
            data={"hash": mobsf_hash},
        )
        r.raise_for_status()
        return r.content


async def is_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.MOBSF_URL}/api/v1/version",
                                 headers=_headers())
            return r.status_code == 200
    except Exception:
        return False
