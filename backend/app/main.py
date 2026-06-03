"""Enci-Intel Backend — FastAPI Application Entry Point"""
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.routers import dashboard, alerts, agents, products, market, chat, reports
from app.routers.admin import router as admin_router
from app.routers.internal import router as internal_router

logger = structlog.get_logger()
settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="Enci-Intel API",
    description="Plataforma de Inteligencia de Mercado Veterinario — Encipharm",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(alerts.router,    prefix="/api/v1", tags=["Alertas"])
app.include_router(agents.router,    prefix="/api/v1", tags=["Agentes"])
app.include_router(products.router,  prefix="/api/v1", tags=["Productos"])
app.include_router(market.router,    prefix="/api/v1", tags=["Mapa Competitivo"])
app.include_router(chat.router,      prefix="/api/v1", tags=["Consultor Vet IA"])
app.include_router(reports.router,   prefix="/api/v1", tags=["Reportes"])
app.include_router(admin_router,     prefix="/api/v1", tags=["Admin Usuarios"])
app.include_router(internal_router,  prefix="/internal", tags=["Internal"])

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "enci-intel-backend", "version": "1.0.0"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Error interno del servidor."}},
    )
