# app/models/quiz_session.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.qna import QuestionWithAnswers
from app.models.category import Category

class QuizSessionBase(BaseModel):
    category_id: int
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class QuizSessionCreate(QuizSessionBase):
    pass

class QuizSessionInDB(QuizSessionBase):
    session_id: int
    create_at: datetime
    update_at: datetime

class QuizSession(QuizSessionInDB):
    pass

class SessionQuestionBase(BaseModel):
    session_id: int
    question_id: int
    order_num: int
    is_answered: str = Field("N", regex='^[YN]$')
    is_correct: str = Field("N", regex='^[YN]$')

class SessionQuestionCreate(SessionQuestionBase):
    pass

class SessionQuestionInDB(SessionQuestionBase):
    sq_id: int
    answer_time: Optional[datetime] = None

class SessionQuestion(SessionQuestionInDB):
    pass

class QuizSessionWithStats(QuizSession):
    """퀴즈 세션 정보와 통계"""
    question_count: int
    completed_count: int = 0
    correct_count: int = 0
    category: Optional[Category] = None

class QuizSessionWithQuestions(QuizSession):
    """퀴즈 세션 정보와 문제 목록"""
    questions: List[QuestionWithAnswers] = []
    category: Optional[Category] = None