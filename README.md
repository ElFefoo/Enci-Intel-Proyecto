# Enci-Intel 🐾

> Sistema de Inteligencia Competitiva del Mercado Veterinario Chileno
> **Encipharm** · v1.0.0 MVP

## Stack Técnico

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + Python 3.12 |
| Frontend | React + TypeScript + Tailwind CSS |
| Base de datos | Firestore (GCP) |
| Autenticación | Keycloak + JWT |
| IA | Vertex AI (Gemini) |
| Despliegue | Cloud Run (GCP) |
| Jobs asíncronos | Cloud Tasks |

## Estructura del Proyecto

```
Enci-Intel-Proyecto/
├── backend/          # FastAPI app
│   ├── app/
│   │   ├── agents/   # 5 agentes de inteligencia competitiva
│   │   ├── middleware/
│   │   ├── routers/
│   │   └── services/
│   └── tests/
├── frontend/         # React + TypeScript
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── store/
│       └── types/
├── infra/            # Scripts GCP
├── docker-compose.yml
└── .github/workflows/ # CI/CD
```

## Setup Local

```bash
# 1. Clonar
git clone https://github.com/ElFefoo/Enci-Intel-Proyecto.git
cd Enci-Intel-Proyecto

# 2. Variables de entorno
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Editar .env con tus valores

# 3. Levantar con Docker Compose
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# Keycloak:  http://localhost:8080
```

## Setup GCP (producción)

```bash
# Configurar proyecto GCP por primera vez
bash infra/setup-gcp.sh
```

## Módulos

- 📊 **Dashboard** — KPIs, alertas recientes, estado agentes
- 🔔 **Alertas** — PRICECHANGE, NEWSKU, STOCKOUT, NEWS
- 🤖 **Agentes IA** — 5 agentes autónomos de monitoreo
- 📦 **Productos** — Catálogo por competidor y categoría
- 🗺️ **Mapa Competitivo** — Visualización del mercado
- 💬 **Consultor Veterinario IA** — Chat con Gemini
- 📄 **Reportes** — PDF / XLSX

## CI/CD

Los workflows en `.github/workflows/` se activan automáticamente al hacer push a `main`:
- `backend-ci.yml` → test + deploy backend a Cloud Run
- `frontend-ci.yml` → build + deploy frontend a Cloud Run

### Secrets requeridos en GitHub

| Secret | Descripción |
|---|---|
| `GCP_PROJECT_ID` | ID del proyecto GCP |
| `GCP_SA_KEY` | JSON del Service Account |
