from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import create_access_token, verify_password
from models.log import LogEntry
from models.user import User
from schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authentification JWT — retourne un token d'accès."""
    user = db.query(User).filter(User.email == payload.email).first()

    # Même message d'erreur que l'utilisateur n'existe pas ou que le mot de passe
    # soit incorrect — évite l'énumération d'utilisateurs (OWASP)
    if not user or not verify_password(payload.password, user.password_hash):
        _log_action(db, None, "LOGIN_FAILED", request, f"email={payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    token = create_access_token({"sub": str(user.id_user), "role": user.role.name})
    _log_action(db, user.id_user, "LOGIN_SUCCESS", request)

    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _log_action(db: Session, user_id, action: str, request: Request, detail: str = ""):
    entry = LogEntry(
        id_user=user_id,
        action=f"{action} {detail}".strip(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(entry)
    db.commit()
