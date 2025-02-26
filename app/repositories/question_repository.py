# app/repositories/question_repository.py
import logging
from typing import List, Optional
from asyncmy import Connection
from app.models.question import Question, QuestionCreate, QuestionUpdate
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class QuestionRepository(BaseRepository[Question]):
    """질문 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "question"
    model_class = Question
    id_column = "question_id"

    @classmethod
    async def create(cls, question: QuestionCreate, conn: Connection = None) -> int:
        """새 질문 생성"""
        query = """
        INSERT INTO question (category_id, answer_type, question_text, note, link_url)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            question.category_id,
            question.answer_type,
            question.question_text,
            question.note,
            question.link_url
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_all_by_category(cls,
                                  category_id: Optional[int] = None,
                                  skip: int = 0,
                                  limit: int = 100,
                                  conn: Connection = None) -> List[Question]:
        """카테고리별 질문 조회 (페이지네이션 포함)"""
        where_clause = "category_id = %s" if category_id else ""
        params = (category_id,) if category_id else None

        return await cls.get_all(
            where_clause=where_clause,
            params=params,
            order_by="question_id DESC",
            limit=limit,
            offset=skip,
            conn=conn
        )

    @classmethod
    async def update(cls, question_id: int, question_update: QuestionUpdate, conn: Connection = None) -> bool:
        """질문 업데이트"""
        # 베이스 클래스의 update 메서드 활용
        return await super().update(question_id, question_update, conn)