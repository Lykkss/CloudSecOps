from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import Base, engine
from routers import auth, health, users

# Création des tables au démarrage (remplacer par Alembic en prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CloudSecOps API",
    description="Backend sécurisé — JWT, RBAC, PostgreSQL",
    version="1.0.0",
    docs_url="/docs" if True else None,  # Désactiver en prod
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
