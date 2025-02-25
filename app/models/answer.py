# app/models/answer.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class AnswerBase(BaseModel):
    question_id: int
    answer_text: str
    is_correct: str = Field(..., regex='^[YN]$')  # "Y" 또는 "N"만 허용


class AnswerCreate(AnswerBase):
    note: Optional[str] = None


class AnswerUpdate(BaseModel):
    answer_text: Optional[str] = None
    is_correct: Optional[str] = None
    note: Optional[str] = None


class AnswerInDB(AnswerBase):
    answer_id: int
    note: Optional[str] = None
    create_at: datetime
    update_at: datetime


class Answer(AnswerInDB):
    pass


# 문제와 답변을 함께 보여주는 모델
class QuestionWithAnswers(Question):
    answers: List[Answer] = []


# 사용자가 제출한 답변 검증용 모델
class SubmitAnswer(BaseModel):
    question_id: int
    selected_answer_ids: List[int]