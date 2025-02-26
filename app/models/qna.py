# app/models/qna.py
from typing import List, Optional
from pydantic import BaseModel
from app.models.question import Question
from app.models.answer import Answer
from app.models.category import Category


class QuestionWithAnswers(Question):
    """문제와 답변을 함께 보여주는 모델"""
    answers: List[Answer] = []
    category: Optional[Category] = None


class QuestionWithCategory(Question):
    """카테고리 정보가 포함된 질문 모델"""
    category: Category