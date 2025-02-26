# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any
from app.models.user import UserCreate, UserLogin, UserUpdate, User
from app.services.user_service import UserService
from app.api.dependencies import get_current_active_user
from app.core.exceptions import ValidationException, UnauthorizedException, NotFoundException, DatabaseException

router = APIRouter()

@router.post("/register", response_model=Dict[str, Any])
async def register(user_data: UserCreate = Body(...)):
    """새 사용자 등록"""
    try:
        return await UserService.register(user_data)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 등록 중 오류 발생: {str(e)}"
        )

@router.post("/login", response_model=Dict[str, Any])
async def login(login_data: UserLogin = Body(...)):
    """사용자 로그인"""
    try:
        return await UserService.login(login_data)
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 중 오류 발생: {str(e)}"
        )

@router.post("/login/access-token", response_model=Dict[str, Any])
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 호환 토큰 로그인 (외부 클라이언트 지원용)"""
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    try:
        result = await UserService.login(login_data)
        return {
            "access_token": result["access_token"],
            "token_type": "bearer"
        }
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 중 오류 발생: {str(e)}"
        )

@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """현재 로그인한 사용자 정보 조회"""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "username": current_user.username,
        "is_admin": current_user.is_admin == "Y",
        "is_active": current_user.is_active == "Y",
        "create_at": current_user.create_at,
        "update_at": current_user.update_at
    }

@router.put("/me", response_model=Dict[str, Any])
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """현재 로그인한 사용자 정보 업데이트"""
    try:
        return await UserService.update_user(current_user.user_id, user_update)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보 업데이트 중 오류 발생: {str(e)}"
        )