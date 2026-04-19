from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from core.database import Base

# Table de liaison rôle ↔ permission (many-to-many)
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("id_role", Integer, ForeignKey("role.id_role"), primary_key=True),
    Column("id_permis", Integer, ForeignKey("permission.id_permis"), primary_key=True),
)


class Role(Base):
    __tablename__ = "role"

    id_role = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permission"

    id_permis = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), unique=True, nullable=False)
    description = Column(String, nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class User(Base):
    __tablename__ = "user_account"

    id_user = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    id_role = Column(Integer, ForeignKey("role.id_role"), nullable=False)

    role = relationship("Role", back_populates="users")
    logs = relationship("LogEntry", back_populates="user")
