# Enci-Intel — Plataforma de Inteligencia de Mercado

> Encipharm · Sistema de inteligencia competitiva para el mercado veterinario chileno

## Stack Técnico
- **Backend**: FastAPI + Python 3.12 → Cloud Run (GCP)
- **Frontend**: React + TypeScript + Vite → Cloud Run (GCP)
- **Base de datos**: Firestore (GCP)
- **Autenticación**: Keycloak + JWT (roles: Admin, Comercial, Gerencia)
- **IA**: Vertex AI (Gemini) — Consultor Veterinario
- **Jobs**: Cloud Tasks + Cloud Scheduler

## Inicio Rápido

```bash
# 1. Levantar servicios en local
docker-compose up -d

# Backend → http://localhost:8000/docs
# Frontend → http://localhost:5173
# Keycloak → http://localhost:8080
```

## Variables de Entorno
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Editar valores según tu entorno
```

## Despliegue GCP
```bash
# Setup inicial (solo una vez)
bash infra/setup-gcp.sh

# Deploy
gcloud run deploy enci-intel-backend --source ./backend --region us-central1
gcloud run deploy enci-intel-frontend --source ./frontend --region us-central1
```

## Estructura
```
enci-intel/
├── backend/          # FastAPI Python 3.12
│   └── app/
│       ├── agents/   # 5 agentes autónomos
│       ├── routers/  # 8 módulos API REST
│       ├── middleware/auth.py  # JWT Keycloak
│       └── services/ # Firestore client
├── frontend/         # React + TypeScript + Vite
│   └── src/
│       ├── pages/    # Dashboard, Alerts, Agents...
│       ├── components/layout/
│       └── store/    # Zustand auth state
├── infra/            # Scripts GCP + Firestore indexes
├── .github/workflows/ # CI/CD GitHub Actions
└── docker-compose.yml
```

## Agentes IA

| ID | Nombre | Frecuencia | Alerta |
|---|---|---|---|
| `agent-isp-surveillance` | Vigilancia ISP | Diaria | `NEWREGISTRATION` |
| `agent-customs-intelligence` | Inteligencia Aduanera | Mensual | Tendencias importación |
| `agent-competitive-monitoring` | Monitoreo Competitivo | Diaria 08:00 | `NEWS` / `NEWSKU` |
| `agent-price-benchmark` | Benchmarking Precios | Continua | `PRICECHANGE` |
| `agent-alert-engine` | Motor de Alertas | Reactivo | `STOCKOUT` / priorización |
