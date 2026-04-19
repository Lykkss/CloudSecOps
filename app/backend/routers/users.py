from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import hash_password
from dependencies.auth import get_current_user, require_role
from models.user import Role, User
from schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté."""
    return _to_response(current_user)


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    """Liste tous les utilisateurs — admin uniquement."""
    return [_to_response(u) for u in db.query(User).all()]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    """Crée un utilisateur — admin uniquement."""
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Désactive un utilisateur (soft delete) — admin uniquement."""
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
