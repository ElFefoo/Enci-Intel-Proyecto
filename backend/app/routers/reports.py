from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.middleware.auth import CurrentUser, get_current_user
from app.services.firestore_service import get_firestore

router = APIRouter()

class ReportRequest(BaseModel):
    type: str
    format: str = "pdf"
    period: Optional[str] = None
    competitors: Optional[list[str]] = None

@router.post("/reports/generate")
async def generate_report(body: ReportRequest, user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    # TODO: encolar en Cloud Tasks
    return {"success": True, "data": {"jobId": "report-placeholder", "status": "queued"}}

@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: str, user: CurrentUser = Depends(get_current_user)):
    return {"success": True, "data": {"jobId": report_id, "status": "pending"}}

@router.get("/reports/{report_id}/download")
async def download_report(report_id: str, user: CurrentUser = Depends(get_current_user)):
    return {"success": True, "data": {"url": None}}
