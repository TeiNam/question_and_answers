# app/api/routes/jwt_test.py
from typing import Dict, Any

from fastapi import APIRouter, Depends

from app.api.dependencies import get_token_data, get_current_user, get_current_admin_user
from app.models.user import User

router = APIRouter()

@router.get("/token-data", response_model=Dict[str, Any])
async def get_jwt_token_info(token_data: Dict = Depends(get_token_data)):
    """JWT 토큰에 포함된 데이터 확인"""
    return {
        "token_info": token_data
    }

@router.get("/user-role", response_model=Dict[str, Any])
async def check_user_role(
    token_data: Dict = Depends(get_token_data),
    current_user: User = Depends(get_current_user)
):
    """사용자 정보와 JWT 토큰의 역할 정보 확인"""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "db_role": current_user.role,
        "db_is_admin": current_user.is_admin == "Y",
        "token_role": token_data.get("role"),
        "token_is_admin": token_data.get("is_admin", False)
    }

@router.get("/admin-only", response_model=Dict[str, Any])
async def admin_only_endpoint(current_user: User = Depends(get_current_admin_user)):
    """관리자만 접근 가능한 엔드포인트 (JWT 토큰으로 확인)"""
    return {
        "message": "관리자 전용 페이지에 접근했습니다.",
        "user_id": current_user.user_id,
        "username": current_user.username
    }

async def creator_role_checker(current_user: User = Depends(get_current_user)):
    """출제자 역할 확인 함수"""
    if current_user.role != "creator":
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("출제자 역할이 필요합니다.")
    return current_user

@router.get("/creator-only", response_model=Dict[str, Any])
async def creator_only_endpoint(current_user: User = Depends(creator_role_checker)):
    """출제자 역할을 가진 사용자만 접근 가능한 엔드포인트"""
    return {
        "message": "출제자 전용 페이지에 접근했습니다.",
        "user_id": current_user.user_id,
        "username": current_user.username
    }