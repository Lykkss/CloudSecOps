"""Fixtures partagées — base de données en mémoire SQLite pour les tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from core.security import hash_password
from main import app
from models.user import Role, User

# SQLite en mémoire — pas besoin de PostgreSQL pour les tests unitaires
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Crée les tables et insère les données de test."""
    Base.metadata.create_all(bind=engine)

    db = TestingSession()
    # Rôles
    admin_role = Role(name="admin", description="Administrateur")
    user_role  = Role(name="user",  description="Utilisateur standard")
    db.add_all([admin_role, user_role])
    db.flush()

    # Comptes
    db.add(User(
        email="admin@test.dev",
        password_hash=hash_password("Admin1234!"),
        id_role=admin_role.id_role,
        is_active=True,
    ))
    db.add(User(
        email="user@test.dev",
        password_hash=hash_password("User1234!"),
        id_role=user_role.id_role,
        is_active=True,
    ))
    db.add(User(
        email="inactive@test.dev",
        password_hash=hash_password("Inactive1!"),
        id_role=user_role.id_role,
        is_active=False,
    ))
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client(setup_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/auth/login", json={"email": "admin@test.dev", "password": "Admin1234!"})
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def user_token(client):
    r = client.post("/auth/login", json={"email": "user@test.dev", "password": "User1234!"})
    return r.json()["access_token"]
