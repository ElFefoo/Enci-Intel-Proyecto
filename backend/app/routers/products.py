from fastapi import APIRouter, Depends, Query
from app.middleware.auth import get_current_user
from app.services.firestore_service import get_db

router = APIRouter()


@router.get("/products")
async def list_products(
    competitor: str | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(20, le=100),
    cursor: str | None = Query(None),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/products"""
    return {"success": True, "data": [], "meta": {"total": 0, "hasMore": False, "nextCursor": None}}


@router.get("/products/{product_id}/price-history")
async def price_history(
    product_id: str,
    days: int = Query(30),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """GET /api/v1/products/{id}/price-history"""
    return {"success": True, "data": {"productId": product_id, "history": []}}
