from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from core.config import settings

_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Security(_header)) -> str:
    """Vérifie la clé API pour les appels machine-to-machine (CI)."""
    if key != settings.CI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide",
        )
    return key
