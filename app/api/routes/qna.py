# app/api/routes/qna.py
from fastapi import APIRouter, Depends, Query, Path, Body, status
from typing import List, Optional
from app.models.question import QuestionCreate, QuestionUpdate
from app.models.answer import AnswerCreate, AnswerUpdate
from app.models.submit import SubmitAnswer
from app.models.qna import QuestionWithAnswers
from app.services.qna_service import QnAService

router = APIRouter()


@router.post("/questions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_question_with_answers(
        question: QuestionCreate = Body(...),
        answers: List[AnswerCreate] = Body(..., min_items=1)
):
    """질문과 답변 생성"""
    return await QnAService.create_question_with_answers(question, answers)


@router.get("/questions/{question_id}", response_model=QuestionWithAnswers)
async def get_question_with_answers(
        question_id: int = Path(..., title="질문 ID", ge=1)
):
    """특정 질문과 답변들 조회"""
    return await QnAService.get_question_with_answers(question_id)


@router.get("/questions", response_model=List[QuestionWithAnswers])
async def get_all_questions_with_answers(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        category_id: Optional[int] = Query(None, ge=1)
):
    """모든 질문과 답변 목록 조회"""
    return await QnAService.get_all_questions_with_answers(skip, limit, category_id)


@router.put("/questions/{question_id}", response_model=dict)
async def update_question(
        question_update: QuestionUpdate,
        question_id: int = Path(..., title="질문 ID", ge=1)
):
    """질문 업데이트"""
    return await QnAService.update_question(question_id, question_update)


@router.put("/answers/{answer_id}", response_model=dict)
async def update_answer(
        answer_update: AnswerUpdate,
        answer_id: int = Path(..., title="답변 ID", ge=1)
):
    """답변 업데이트"""
    return await QnAService.update_answer(answer_id, answer_update)


@router.delete("/questions/{question_id}", response_model=dict)
async def delete_question(
        question_id: int = Path(..., title="질문 ID", ge=1)
):
    """질문 및 관련 답변 삭제"""
    return await QnAService.delete_question(question_id)


@router.post("/submit", response_model=dict)
async def check_answer(
        submit_data: SubmitAnswer
):
    """사용자 답변 제출 및 채점"""
    return await QnAService.check_answers(
        submit_data.question_id,
        submit_data.selected_answer_ids
    )