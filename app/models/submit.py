# app/models/submit.py
from pydantic import BaseModel, Field
from typing import List

class SubmitAnswer(BaseModel):
    """사용자가 제출한 답변 검증용 모델"""
    question_id: int = Field(..., ge=1)
    selected_answer_ids: List[int] = Field(..., min_items=1)