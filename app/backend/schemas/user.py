from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role_id: int = 2  # Par défaut : rôle "user"


class UserResponse(BaseModel):
    id_user: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    role: str

    model_config = {"from_attributes": True}
