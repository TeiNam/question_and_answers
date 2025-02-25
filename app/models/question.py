# app/models/question.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.answer import Answer


class QuestionBase(BaseModel):
    category: str = Field(..., max_length=20)
    question_text: str
    answer_type: int = Field(1, ge=1, le=2)  # 1: 한 개 정답, 2: 여러 개 정답


class QuestionCreate(QuestionBase):
    note: Optional[str] = None
    link_url: Optional[str] = None


class QuestionUpdate(BaseModel):
    category: Optional[str] = None
    question_text: Optional[str] = None
    answer_type: Optional[int] = None
    note: Optional[str] = None
    link_url: Optional[str] = None


class QuestionInDB(QuestionBase):
    question_id: int
    note: Optional[str] = None
    link_url: Optional[str] = None
    create_at: datetime
    update_at: datetime


class Question(QuestionInDB):
    pass


# 문제와 답변을 함께 보여주는 모델
class QuestionWithAnswers(Question):
    answers: List[Answer] = []