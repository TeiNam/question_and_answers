# app/models/answer.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class AnswerBase(BaseModel):
    question_id: int
    answer_text: str
    is_correct: str = Field(..., pattern='^[YN]$')  # "Y" 또는 "N"만 허용


class AnswerCreate(AnswerBase):
    note: Optional[str] = None


class AnswerUpdate(BaseModel):
    answer_text: Optional[str] = None
    is_correct: Optional[str] = None
    note: Optional[str] = None

    @validator('is_correct')
    def validate_is_correct(cls, v):
        if v is not None and v not in ["Y", "N"]:
            raise ValueError("is_correct는 'Y' 또는 'N'이어야 합니다.")
        return v


class AnswerInDB(AnswerBase):
    answer_id: int
    note: Optional[str] = None
    create_at: datetime
    update_at: datetime


class Answer(AnswerInDB):
    pass