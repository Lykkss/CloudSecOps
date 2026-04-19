from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import hash_password
from dependencies.auth import get_current_user, require_role
from models.user import Role, User
from schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Mon profil",
    responses={
        200: {"description": "Profil de l'utilisateur courant"},
        401: {"description": "Token absent ou invalide"},
    },
)
def get_me(current_user: User = Depends(get_current_user)):
    """Retourne les informations du compte authentifié (id, email, rôle, statut)."""
    return _to_response(current_user)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Liste des utilisateurs",
    responses={
        200: {"description": "Liste complète des comptes"},
        401: {"description": "Token absent ou invalide"},
        403: {"description": "Rôle admin requis"},
    },
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    """Retourne tous les comptes (actifs et inactifs) — **admin uniquement**."""
    return [_to_response(u) for u in db.query(User).all()]


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un utilisateur",
    responses={
        201: {"description": "Compte créé"},
        401: {"description": "Token absent ou invalide"},
        403: {"description": "Rôle admin requis"},
        404: {"description": "Rôle introuvable"},
        409: {"description": "Email déjà utilisé"},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "new_user": {
                            "summary": "Nouvel utilisateur standard",
                            "value": {"email": "alice@example.com", "password": "P@ssw0rd!", "role_id": 2},
                        }
                    }
                }
            }
        }
    },
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    """Crée un nouveau compte utilisateur — **admin uniquement**.

    - `role_id = 1` → admin
    - `role_id = 2` → user (lecture seule)
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    role = db.query(Role).filter(Role.id_role == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rôle introuvable")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        id_role=payload.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_response(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Désactiver un utilisateur",
    responses={
        204: {"description": "Utilisateur désactivé (soft delete)"},
        400: {"description": "Impossible de se désactiver soi-même"},
        401: {"description": "Token absent ou invalide"},
        403: {"description": "Rôle admin requis"},
        404: {"description": "Utilisateur introuvable"},
    },
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Désactive un compte (soft delete — `is_active = false`) — **admin uniquement**.

    L'utilisateur ne peut pas se désactiver lui-même.
    """
    if user_id == current_user.id_user:
        raise HTTPException(status_code=400, detail="Impossible de se désactiver soi-même")

    user = db.query(User).filter(User.id_user == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.is_active = False
    db.commit()


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id_user=user.id_user,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        role=user.role.name,
    )
