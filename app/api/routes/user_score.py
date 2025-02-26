# app/api/routes/user_score.py
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query, Path, status, HTTPException

from app.api.dependencies import get_current_active_user
from app.core.exceptions import NotFoundException
from app.models.submit import SubmitAnswer
from app.models.user import User
from app.models.user_score import UserScore, UserScoreSummary
from app.services.user_score_service import UserScoreService

router = APIRouter()

@router.post("/submit", response_model=Dict[str, Any])
async def submit_answer(
    submit_data: SubmitAnswer,
    current_user: User = Depends(get_current_active_user)
):
    """사용자 답변 제출 및 결과 기록"""
    try:
        return await UserScoreService.record_user_answer(current_user.user_id, submit_data)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"답변 제출 중 오류 발생: {str(e)}"
        )

@router.get("/history", response_model=List[UserScore])
async def get_score_history(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
):
    """사용자의 성적 기록 조회"""
    try:
        return await UserScoreService.get_user_scores(current_user.user_id, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"성적 기록 조회 중 오류 발생: {str(e)}"
        )

@router.get("/summary", response_model=UserScoreSummary)
async def get_score_summary(
    current_user: User = Depends(get_current_active_user)
):
    """사용자의 성적 요약 정보 조회"""
    try:
        return await UserScoreService.get_user_score_summary(current_user.user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"성적 요약 조회 중 오류 발생: {str(e)}"
        )

@router.get("/category/{category_id}", response_model=List[UserScore])
async def get_category_scores(
    category_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_user)
):
    """특정 카테고리에 대한 사용자 성적 조회"""
    try:
        # 카테고리의 사용자 성적 조회 기능을 구현해야 함
        # 서비스와 레포지토리에 해당 메서드 추가 필요
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="이 기능은 아직 구현되지 않았습니다."
        )
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"카테고리 성적 조회 중 오류 발생: {str(e)}"
        )