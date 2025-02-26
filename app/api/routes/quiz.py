# app/api/routes/quiz.py
from typing import List

from fastapi import APIRouter, Depends, Query, Path, Body, status, HTTPException

from app.api.dependencies import get_current_active_user
from app.core.exceptions import NotFoundException
from app.models.quiz_session import QuizSessionCreate, QuizSessionWithStats
from app.models.submit import SubmitAnswer
from app.models.user import User
from app.services.quiz_service import QuizService

router = APIRouter()

@router.post("/sessions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_quiz_session(
    session: QuizSessionCreate,
    question_count: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user)
):
    """카테고리별 퀴즈 세션 생성 (로그인 필요)"""
    try:
        return await QuizService.create_quiz_session(session, question_count)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"퀴즈 세션 생성 중 오류 발생: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=QuizSessionWithStats)
async def get_quiz_session(
    session_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_user)
):
    """퀴즈 세션 정보 조회 (로그인 필요)"""
    try:
        return await QuizService.get_quiz_session(session_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"퀴즈 세션 조회 중 오류 발생: {str(e)}"
        )

@router.get("/categories/{category_id}/sessions", response_model=List[QuizSessionWithStats])
async def get_category_sessions(
    category_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_user)
):
    """카테고리별 퀴즈 세션 목록 조회 (로그인 필요)"""
    try:
        return await QuizService.get_category_sessions(category_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"퀴즈 세션 목록 조회 중 오류 발생: {str(e)}"
        )

@router.post("/sessions/{session_id}/submit", response_model=dict)
async def submit_session_answer(
    session_id: int = Path(..., ge=1),
    submit_data: SubmitAnswer = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """세션 내 문제 답변 제출 (로그인 필요)"""
    try:
        return await QuizService.submit_session_answer(
            session_id,
            submit_data.question_id,
            submit_data.selected_answer_ids,
            current_user.user_id
        )
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"답변 제출 중 오류 발생: {str(e)}"
        )

@router.get("/sessions/{session_id}/questions", response_model=List[dict])
async def get_session_questions(
    session_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_active_user)
):
    """세션에 포함된 문제 목록 조회 (로그인 필요)"""
    try:
        return await QuizService.get_session_questions(session_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 문제 목록 조회 중 오류 발생: {str(e)}"
        )

@router.get("/my-sessions", response_model=List[QuizSessionWithStats])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """현재 사용자의 퀴즈 세션 목록 조회 (로그인 필요)"""
    try:
        return await QuizService.get_user_sessions(current_user.user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 세션 목록 조회 중 오류 발생: {str(e)}"
        )