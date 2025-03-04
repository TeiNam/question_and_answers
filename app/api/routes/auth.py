# app/api/routes/auth.py
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_current_active_user, get_current_admin_user, get_token_data
from app.core.exceptions import ValidationException, UnauthorizedException, ForbiddenException, NotFoundException
from app.models.user import UserCreate, UserLogin, UserUpdate, User
from app.services.user_service import UserService

router = APIRouter()


# 공통 API 엔드포인트 (인증 불필요)
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
    """일반 사용자 로그인"""
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


@router.post("/admin/login", response_model=Dict[str, Any])
async def admin_login(login_data: UserLogin = Body(...)):
    """관리자 로그인"""
    try:
        return await UserService.admin_login(login_data)
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail)
        )
    except ForbiddenException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"관리자 로그인 중 오류 발생: {str(e)}"
        )


@router.post("/login/access-token", response_model=Dict[str, Any])
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 호환 토큰 로그인 (외부 클라이언트 지원용)"""
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    try:
        # 관리자용 클라이언트 식별을 위한 scope 확인 (선택적)
        is_admin_client = "admin" in form_data.scopes

        if is_admin_client:
            result = await UserService.admin_login(login_data)
        else:
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
    except ForbiddenException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 중 오류 발생: {str(e)}"
        )


# 일반 사용자 API 엔드포인트 (일반 로그인 필요)
@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """현재 로그인한 사용자 정보 조회"""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
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


@router.get("/solvers", response_model=List[Dict[str, Any]])
async def get_solvers(current_user: User = Depends(get_current_active_user)):
    """풀이자 목록 조회 (모든 사용자가 접근 가능)"""
    try:
        solvers = await UserService.get_users_by_role("solver", current_user.user_id, check_admin=False)

        return [
            {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role
            }
            for user in solvers
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"풀이자 목록 조회 중 오류 발생: {str(e)}"
        )


# 관리자 API 엔드포인트 (관리자 권한 필요)
@router.get("/admin/users", response_model=List[Dict[str, Any]])
async def get_all_users(
        role: Optional[str] = Query(None, description="사용자 역할 필터링 (admin, creator, solver)"),
        current_user: User = Depends(get_current_admin_user)  # 관리자만 접근 가능
):
    """사용자 목록 조회 (관리자 전용)
    role 매개변수를 제공하면 특정 역할의 사용자만 필터링하여 조회"""
    try:
        if role:
            users = await UserService.get_users_by_role(role, current_user.user_id)
        else:
            users = await UserService.get_all_users(current_user.user_id)

        return [
            {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active == "Y",
                "is_admin": user.is_admin == "Y",
                "create_at": user.create_at
            }
            for user in users
        ]
    except ForbiddenException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e.detail)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 목록 조회 중 오류 발생: {str(e)}"
        )


@router.get("/admin/users/{user_id}", response_model=Dict[str, Any])
async def get_user_detail(
        user_id: int = Path(..., ge=1, description="조회할 사용자 ID"),
        current_user: User = Depends(get_current_admin_user)  # 관리자만 접근 가능
):
    """특정 사용자 상세 정보 조회 (관리자 전용)"""
    try:
        user = await UserService.get_user_by_id(user_id)

        return {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active == "Y",
            "is_admin": user.is_admin == "Y",
            "create_at": user.create_at,
            "update_at": user.update_at
        }
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 정보 조회 중 오류 발생: {str(e)}"
        )


@router.put("/admin/users/{user_id}", response_model=Dict[str, Any])
async def update_user(
        user_update: UserUpdate,
        user_id: int = Path(..., ge=1, description="수정할 사용자 ID"),
        current_user: User = Depends(get_current_admin_user)  # 관리자만 접근 가능
):
    """특정 사용자 정보 업데이트 (관리자 전용)"""
    try:
        return await UserService.update_user(user_id, user_update, is_admin=True)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
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