import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.database import Base, engine
from routers import ai, auth, ebios, export, health, incidents, logs, mobile_scans, reports, scans, users

Base.metadata.create_all(bind=engine)

_DESCRIPTION = """
## CloudSecOps — API de gestion sécurisée

Architecture **Zero Trust** avec authentification JWT et contrôle d'accès RBAC.

### Flux d'authentification
1. `POST /auth/login` → obtenir un `access_token`
2. Cliquer **Authorize** (🔒) en haut à droite, saisir `Bearer <token>`
3. Appeler les endpoints protégés

### Rôles
| Rôle  | Permissions |
|-------|-------------|
| `admin` | Lecture + création + suppression d'utilisateurs, accès logs |
| `user`  | Lecture de son propre profil uniquement |

### Sécurité
- Mots de passe hashés **bcrypt** (coût 12)
- Tokens **JWT HS256** — expiration configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`
- Logs d'audit sur chaque action sensible
"""

_TAGS = [
    {"name": "auth",      "description": "Authentification — obtenir et valider un JWT"},
    {"name": "users",     "description": "Gestion des comptes utilisateurs (RBAC)"},
    {"name": "scans",     "description": "Résultats de scans de vulnérabilités (Trivy)"},
    {"name": "incidents", "description": "Incidents de sécurité et simulations (IAM compromise…)"},
    {"name": "reports",   "description": "Rapports d'investigation forensique"},
    {"name": "mobile",    "description": "Analyse de sécurité mobile (MobSF / APK)"},
    {"name": "ebios",     "description": "Analyse des risques EBIOS Risk Manager"},
    {"name": "ai",        "description": "Assistant IA local (Ollama)"},
    {"name": "logs",      "description": "Logs CloudWatch / AWS"},
    {"name": "export",    "description": "Export PDF des rapports"},
    {"name": "health",    "description": "Vérification de l'état du service"},
]

app = FastAPI(
    title="CloudSecOps API",
    description=_DESCRIPTION,
    version="1.0.0",
    openapi_tags=_TAGS,
    contact={"name": "CloudSecOps", "email": "admin@cloudsecops.dev"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://52.47.190.170",
        "http://52.47.190.170:3000",
        "http://52.47.190.170:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(scans.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(mobile_scans.router)
app.include_router(ebios.router)
app.include_router(ai.router)
app.include_router(logs.router)
app.include_router(export.router)

# ── Frontend React (dist) ou fallback HTML ────────────────────────────────────
_BASE       = os.path.dirname(__file__)
_DIST_DIR   = os.path.join(_BASE, "..", "frontend", "dist")
_ASSETS_DIR = os.path.join(_DIST_DIR, "assets")
_HTML_DIR   = os.path.join(_BASE, "..", "frontend")

if os.path.isdir(_DIST_DIR):
    # Servir les assets compilés React
    app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/login", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    async def serve_spa():
        return FileResponse(os.path.join(_DIST_DIR, "index.html"))

elif os.path.isdir(_HTML_DIR):
    # Fallback : ancien frontend HTML vanilla
    app.mount("/ui", StaticFiles(directory=_HTML_DIR, html=True), name="frontend")