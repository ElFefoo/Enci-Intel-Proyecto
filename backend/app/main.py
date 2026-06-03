from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import dashboard, alerts, agents, products, market, chat, reports, internal

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[Enci-Intel] Iniciando en modo: {settings.APP_ENV}")
    yield
    # Shutdown
    print("[Enci-Intel] Apagando...")


app = FastAPI(
    title="Enci-Intel API",
    description="Inteligencia Competitiva del Mercado Veterinario Chileno",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://enci-intel-frontend-*.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
PREFIX = "/api/v1"
app.include_router(dashboard.router, prefix=PREFIX, tags=["Dashboard"])
app.include_router(alerts.router,    prefix=PREFIX, tags=["Alertas"])
app.include_router(agents.router,    prefix=PREFIX, tags=["Agentes"])
app.include_router(products.router,  prefix=PREFIX, tags=["Productos"])
app.include_router(market.router,    prefix=PREFIX, tags=["Mercado"])
app.include_router(chat.router,      prefix=PREFIX, tags=["Consultor IA"])
app.include_router(reports.router,   prefix=PREFIX, tags=["Reportes"])
app.include_router(internal.router,  prefix="",      tags=["Internal"])


@app.get("/health")
async def health():
    return {"success": True, "data": {"status": "ok", "env": settings.APP_ENV}}
