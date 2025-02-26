# app/models/user_score.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserScoreBase(BaseModel):
    user_id: int
    question_id: int
    is_correct: str = Field("N", regex='^[YN]$')
    selected_answers: str  # 쉼표로 구분된 답변 ID 목록

class UserScoreCreate(UserScoreBase):
    pass

class UserScoreInDB(UserScoreBase):
    score_id: int
    submit_at: datetime

class UserScore(UserScoreInDB):
    pass

class UserCategoryStatBase(BaseModel):
    user_id: int
    category_id: int
    total_questions: int = 0
    correct_answers: int = 0

class UserCategoryStatCreate(UserCategoryStatBase):
    pass

class UserCategoryStatInDB(UserCategoryStatBase):
    stat_id: int
    last_access: datetime

class UserCategoryStat(UserCategoryStatInDB):
    pass

class UserScoreSummary(BaseModel):
    total_questions: int
    correct_answers: int
    accuracy_rate: float
    category_stats: List[UserCategoryStat] = []