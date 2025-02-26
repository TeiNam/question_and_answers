# app/models/question.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QuestionBase(BaseModel):
    category_id: int = Field(..., ge=1)
    user_id: int = Field(..., ge=1)  # 출제자 ID
    answer_type: int = Field(1, ge=1, le=2)  # 1: 한 개 정답, 2: 여러 개 정답
    question_text: str
    note: Optional[str] = None
    link_url: Optional[str] = None
    group_id: Optional[int] = None  # 그룹 ID (특정 그룹에만 공개)


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    category_id: Optional[int] = None
    user_id: Optional[int] = None
    answer_type: Optional[int] = None
    question_text: Optional[str] = None
    note: Optional[str] = None
    link_url: Optional[str] = None
    group_id: Optional[int] = None


class QuestionInDB(QuestionBase):
    question_id: int
    create_at: datetime
    update_at: datetime


class Question(QuestionInDB):
    pass