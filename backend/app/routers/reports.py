from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.middleware.auth import get_current_user
from app.services.firestore_service import get_db

router = APIRouter()


class ReportRequest(BaseModel):
    type: str  # 'weekly' | 'competitor' | 'price_benchmark'
    format: str = "pdf"  # 'pdf' | 'xlsx'
    dateFrom: str | None = None
    dateTo: str | None = None
    competitors: list[str] | None = None


@router.post("/reports/generate")
async def generate_report(
    body: ReportRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """POST /api/v1/reports/generate"""
    # TODO: generar PDF/XLSX y subir a Cloud Storage
    return {"success": True, "data": {"reportId": "pending", "status": "queued", "downloadUrl": None}}


@router.get("/reports")
async def list_reports(
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/reports"""
    return {"success": True, "data": []}
