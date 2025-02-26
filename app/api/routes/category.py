# app/api/routes/category.py
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path, status, HTTPException

from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.core.exceptions import NotFoundException, ValidationException
from app.models.category import Category, CategoryCreate, CategoryUpdate
from app.models.user import User
from app.services.category_service import CategoryService

router = APIRouter()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_admin_user)  # 관리자만 카테고리 생성 가능
):
    """새 카테고리 생성 (관리자 권한 필요)"""
    try:
        return await CategoryService.create_category(category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카테고리 생성 중 오류 발생: {str(e)}"
        )

@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_user)  # 로그인 사용자만 조회 가능
):
    """ID로 카테고리 조회 (로그인 필요)"""
    try:
        return await CategoryService.get_category(category_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카테고리 조회 중 오류 발생: {str(e)}"
        )

@router.get("/", response_model=List[Category])
async def get_all_categories(
    is_use: Optional[str] = Query(None, regex='^[YN]$', description="사용 여부(Y/N)"),
    current_user: User = Depends(get_current_active_user)  # 로그인 사용자만 조회 가능
):
    """모든 카테고리 조회 (로그인 필요)"""
    try:
        return await CategoryService.get_all_categories(is_use)
    except ValidationException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카테고리 목록 조회 중 오류 발생: {str(e)}"
        )

@router.put("/{category_id}", response_model=dict)
async def update_category(
    category_update: CategoryUpdate,
    category_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_admin_user)  # 관리자만 업데이트 가능
):
    """카테고리 업데이트 (관리자 권한 필요)"""
    try:
        return await CategoryService.update_category(category_id, category_update)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카테고리 업데이트 중 오류 발생: {str(e)}"
        )

@router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_admin_user)  # 관리자만 삭제 가능
):
    """카테고리 삭제 (관리자 권한 필요)"""
    try:
        return await CategoryService.delete_category(category_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카테고리 삭제 중 오류 발생: {str(e)}"
        )