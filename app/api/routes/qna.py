# app/api/routes/qna.py
from fastapi import APIRouter, Depends, Query, Path, Body, status, HTTPException
from typing import List, Optional
from app.models.question import QuestionCreate, QuestionUpdate
from app.models.answer import AnswerCreate, AnswerUpdate
from app.models.submit import SubmitAnswer
from app.models.qna import QuestionWithAnswers
from app.models.user import User
from app.services.qna_service import QnAService
from app.core.exceptions import NotFoundException, DatabaseException
from app.api.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.post("/questions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_question_with_answers(
        question: QuestionCreate = Body(...),
        answers: List[AnswerCreate] = Body(..., min_items=1),
        current_user: User = Depends(get_current_admin_user)  # 관리자만 문제 생성 가능
):
    """질문과 답변 생성 (관리자 권한 필요)"""
    try:
        return await QnAService.create_question_with_answers(question, answers)
    except (NotFoundException, DatabaseException) as e:
        # 예외 그대로 전파하여 미들웨어에서 처리
        raise
    except Exception as e:
        # 처리되지 않은 예외는 500 에러로 처리
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질문 및 답변 생성 중 오류 발생: {str(e)}"
        )


@router.get("/questions/{question_id}", response_model=QuestionWithAnswers)
async def get_question_with_answers(
        question_id: int = Path(..., title="질문 ID", ge=1),
        current_user: User = Depends(get_current_active_user)  # 로그인 사용자만 조회 가능
):
    """특정 질문과 답변들 조회 (로그인 필요)"""
    try:
        return await QnAService.get_question_with_answers(question_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질문 조회 중 오류 발생: {str(e)}"
        )


@router.get("/questions", response_model=List[QuestionWithAnswers])
async def get_all_questions_with_answers(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        category_id: Optional[int] = Query(None, ge=1),
        current_user: User = Depends(get_current_active_user)  # 로그인 사용자만 조회 가능
):
    """모든 질문과 답변 목록 조회 (로그인 필요)"""
    try:
        return await QnAService.get_all_questions_with_answers(skip, limit, category_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질문 목록 조회 중 오류 발생: {str(e)}"
        )


@router.put("/questions/{question_id}", response_model=dict)
async def update_question(
        question_update: QuestionUpdate,
        question_id: int = Path(..., title="질문 ID", ge=1),
        current_user: User = Depends(get_current_admin_user)  # 관리자만 업데이트 가능
):
    """질문 업데이트 (관리자 권한 필요)"""
    try:
        return await QnAService.update_question(question_id, question_update)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질문 업데이트 중 오류 발생: {str(e)}"
        )


@router.put("/answers/{answer_id}", response_model=dict)
async def update_answer(
        answer_update: AnswerUpdate,
        answer_id: int = Path(..., title="답변 ID", ge=1),
        current_user: User = Depends(get_current_admin_user)  # 관리자만 업데이트 가능
):
    """답변 업데이트 (관리자 권한 필요)"""
    try:
        return await QnAService.update_answer(answer_id, answer_update)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"답변 업데이트 중 오류 발생: {str(e)}"
        )


@router.delete("/questions/{question_id}", response_model=dict)
async def delete_question(
        question_id: int = Path(..., title="질문 ID", ge=1),
        current_user: User = Depends(get_current_admin_user)  # 관리자만 삭제 가능
):
    """질문 및 관련 답변 삭제 (관리자 권한 필요)"""
    try:
        return await QnAService.delete_question(question_id)
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"질문 삭제 중 오류 발생: {str(e)}"
        )


@router.post("/submit", response_model=dict)
async def check_answer(
        submit_data: SubmitAnswer,
        current_user: User = Depends(get_current_active_user)  # 로그인 사용자만 제출 가능
):
    """사용자 답변 제출 및 채점 (로그인 필요)"""
    try:
        # 여기에 사용자 제출 기록을 저장하는 로직을 추가할 수 있음
        result = await QnAService.check_answers(
            submit_data.question_id,
            submit_data.selected_answer_ids
        )

        # 사용자 ID 추가
        result["user_id"] = current_user.user_id

        return result
    except NotFoundException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"답변 확인 중 오류 발생: {str(e)}"
        )