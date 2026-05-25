#!/bin/bash
# Déploiement rapide EC2 sans rebuild Docker (quand Docker Hub inaccessible)
set -e

EC2="ec2-user@52.47.190.170"
KEY="~/.ssh/cloud-secops.pem"
APP_DIR="$(dirname "$0")/.."

echo "📦 Copie des fichiers sur EC2..."
scp -i $KEY $APP_DIR/app/backend/main.py $EC2:/home/ec2-user/cloudsecops-app/app/backend/main.py
scp -i $KEY -r $APP_DIR/app/frontend/dist $EC2:/home/ec2-user/cloudsecops-app/app/frontend/

echo "🔄 Injection dans le conteneur..."
ssh -i $KEY $EC2 "
  docker cp ~/cloudsecops-app/app/backend/main.py cloudsecops-api:/app/main.py
  docker cp ~/cloudsecops-app/app/frontend/dist cloudsecops-api:/frontend/dist
  docker restart cloudsecops-api
  sleep 5
  curl -s http://localhost:8000/health
"
echo "✅ Déploiement terminé"
