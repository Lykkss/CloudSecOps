FROM python:3.12-slim

WORKDIR /app

# Dépendances système pour WeasyPrint (rendu PDF) et outils réseau
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copie des dépendances en premier (cache Docker)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source backend
COPY backend/ .

# Copie du frontend (servi comme fichiers statiques via /ui)
COPY frontend/ ../frontend/

# Répertoire pour les uploads APK temporaires
RUN mkdir -p /app/uploads

# Installation de apkeep pour téléchargement APK Play Store
RUN curl -L 'https://github.com/EFForg/apkeep/releases/download/0.17.0/apkeep-x86_64-unknown-linux-gnu' \
    -o /usr/local/bin/apkeep && chmod +x /usr/local/bin/apkeep

# Utilisateur non-root (OWASP)
RUN useradd -m appuser && chown -R appuser:appuser /app /frontend /app/uploads 2>/dev/null || true
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
