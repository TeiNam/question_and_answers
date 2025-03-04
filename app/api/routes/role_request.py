# app/api/routes/role_request.py
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Body, Path, HTTPException, status

from app.api.dependencies import get_current_active_user, get_current_admin_user
from app.core.exceptions import ValidationException, NotFoundException, ForbiddenException
from app.models.role_request import RoleRequest, RoleApprovalRequest
from app.models.user import User
from app.services.role_request_service import RoleRequestService

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def create_role_request(
        role: str = Body(..., embed=True),
        reason: str = Body(..., embed=True),
        current_user: User = Depends(get_current_active_user)
):
    """새 역할 변경 요청 생성 (일반 사용자)"""
    try:
        return await RoleRequestService.create_role_request(
            current_user.user_id,
            role,
            reason
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"역할 변경 요청 생성 중 오류 발생: {str(e)}"
        )


@router.get("/me", response_model=List[RoleRequest])
async def get_my_role_requests(current_user: User = Depends(get_current_active_user)):
    """내 역할 변경 요청 내역 조회"""
    try:
        return await RoleRequestService.get_user_requests(current_user.user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"역할 변경 요청 내역 조회 중 오류 발생: {str(e)}"
        )


@router.get("/pending", response_model=List[Dict[str, Any]])
async def get_pending_role_requests(current_user: User = Depends(get_current_admin_user)):
    """관리자용 대기 중인 역할 변경 요청 목록 조회"""
    try:
        return await RoleRequestService.get_pending_requests(current_user.user_id)
    except ForbiddenException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e.detail)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대기 중인 역할 변경 요청 목록 조회 중 오류 발생: {str(e)}"
        )


@router.post("/{request_id}/approve", response_model=Dict[str, Any])
async def approve_role_request(
        approval_data: RoleApprovalRequest,
        request_id: int = Path(..., ge=1),
        current_user: User = Depends(get_current_admin_user)
):
    """역할 변경 요청 승인 (관리자 전용)"""
    try:
        return await RoleRequestService.approve_role_request(
            request_id,
            current_user.user_id,
            approval_data
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
            detail=f"역할 변경 요청 승인 중 오류 발생: {str(e)}"
        )


@router.post("/{request_id}/reject", response_model=Dict[str, Any])
async def reject_role_request(
        rejection_data: RoleApprovalRequest,
        request_id: int = Path(..., ge=1),
        current_user: User = Depends(get_current_admin_user)
):
    """역할 변경 요청 거부 (관리자 전용)"""
    try:
        return await RoleRequestService.reject_role_request(
            request_id,
            current_user.user_id,
            rejection_data
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
            detail=f"역할 변경 요청 거부 중 오류 발생: {str(e)}"
        )
