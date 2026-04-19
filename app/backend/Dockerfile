FROM python:3.12-slim

WORKDIR /app

# Copie des dépendances en premier (cache Docker)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source backend
COPY backend/ .

# Copie du frontend (servi comme fichiers statiques via /ui)
COPY frontend/ ../frontend/

# Utilisateur non-root (OWASP — pas de root dans le conteneur)
RUN useradd -m appuser && chown -R appuser:appuser /app /frontend 2>/dev/null || true
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
