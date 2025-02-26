# app/models/question.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuestionBase(BaseModel):
    category_id: int = Field(..., ge=1)
    question_text: str
    answer_type: int = Field(1, ge=1, le=2)  # 1: 한 개 정답, 2: 여러 개 정답


class QuestionCreate(QuestionBase):
    note: Optional[str] = None
    link_url: Optional[str] = None


class QuestionUpdate(BaseModel):
    category_id: Optional[int] = None
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


# 문제와 답변을 함께 보여주는 모델은 순환 참조를 피하기 위해 별도로 정의