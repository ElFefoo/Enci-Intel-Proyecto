from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.middleware.auth import CurrentUser, get_current_user
from app.services.firestore_service import get_firestore

router = APIRouter()

@router.get("/products/categories")
async def list_categories(user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": []}

@router.get("/products/categories/{category_id}/competitors")
async def list_competitors_by_category(category_id: str, user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": []}

@router.get("/products/categories/{category_id}/competitors/{competitor_id}/products")
async def list_products(
    category_id: str, competitor_id: str,
    limit: int = Query(20, le=100), cursor: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore),
):
    return {"success": True, "data": [], "meta": {"hasMore": False}}

@router.get("/products/{product_id}")
async def get_product(product_id: str, user: CurrentUser = Depends(get_current_user), db=Depends(get_firestore)):
    return {"success": True, "data": {}}
