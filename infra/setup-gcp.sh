#!/bin/bash
# =============================================================================
# Enci-Intel — Setup inicial GCP + Firebase Auth (Identity Platform)
# Ejecutar UNA sola vez al crear el proyecto
# Uso: bash infra/setup-gcp.sh
# =============================================================================
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-enci-intel-prod}"
REGION="${GCP_REGION:-us-central1}"

echo "=> Configurando proyecto: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo "=> Habilitando APIs necesarias..."
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  cloudtasks.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  identitytoolkit.googleapis.com \
  firebase.googleapis.com \
  aiplatform.googleapis.com

echo "=> Creando Firestore en modo nativo..."
gcloud firestore databases create \
  --location="$REGION" \
  --type=firestore-native 2>/dev/null || echo "   Firestore ya existe"

echo "=> Aplicando indices Firestore..."
gcloud firestore indexes composite create \
  --project="$PROJECT_ID" \
  --configuration-file=infra/firestore-indexes.json 2>/dev/null || echo "   Indices ya existen o se aplican manualmente"

echo "=> Creando cola Cloud Tasks para agentes..."
gcloud tasks queues create enci-intel-agents \
  --location="$REGION" \
  --max-attempts=3 \
  --min-backoff=30s \
  --max-backoff=300s 2>/dev/null || echo "   Cola ya existe"

echo "=> Creando Service Account para Cloud Run..."
gcloud iam service-accounts create enci-intel-backend \
  --display-name="Enci-Intel Backend Service Account" 2>/dev/null || echo "   SA ya existe"

SA_EMAIL="enci-intel-backend@${PROJECT_ID}.iam.gserviceaccount.com"

# Permisos necesarios
for ROLE in \
  roles/datastore.user \
  roles/cloudtasks.enqueuer \
  roles/aiplatform.user \
  roles/secretmanager.secretAccessor \
  roles/firebase.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE" --quiet
done

echo ""
echo "============================================================"
echo "  Setup completado. Proximos pasos:"
echo ""
echo "  1. Ir a Firebase Console: https://console.firebase.google.com"
echo "     - Agregar proyecto existente: $PROJECT_ID"
echo "     - Habilitar Authentication > Email/Password"
echo "     - Agregar una app Web y copiar firebaseConfig"
echo "     - Pegar valores en frontend/.env"
echo ""
echo "  2. Crear primer usuario Admin:"
echo "     firebase auth:import o desde Firebase Console > Authentication"
echo "     Luego asignar rol via API: PUT /api/v1/admin/users/{uid}/role"
echo ""
echo "  3. Desplegar backend:"
echo "     gcloud run deploy enci-intel-backend \\"
echo "       --source ./backend \\"
echo "       --region $REGION \\"
echo "       --service-account=$SA_EMAIL \\"
echo "       --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID,FIREBASE_PROJECT_ID=$PROJECT_ID,APP_ENV=production"
echo "============================================================"
