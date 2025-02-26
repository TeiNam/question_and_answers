# app/repositories/answer_repository.py
import logging
from typing import List

from asyncmy import Connection

from app.models.answer import Answer, AnswerCreate
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AnswerRepository(BaseRepository[Answer]):
    """답변 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "answer"
    model_class = Answer
    id_column = "answer_id"

    @classmethod
    async def create(cls, answer: AnswerCreate, conn: Connection = None) -> int:
        """새 답변 생성"""
        query = """
        INSERT INTO answer (question_id, is_correct, answer_text, note)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            answer.question_id,
            answer.is_correct,
            answer.answer_text,
            answer.note
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_by_question_id(cls, question_id: int, conn: Connection = None) -> List[Answer]:
        """질문 ID로 답변들 조회"""
        return await cls.get_all(
            where_clause="question_id = %s",
            params=(question_id,),
            conn=conn
        )

    @classmethod
    async def delete_by_question_id(cls, question_id: int, conn: Connection = None) -> bool:
        """질문 ID로 모든 답변 삭제"""
        query = "DELETE FROM answer WHERE question_id = %s"

        cursor = await cls.execute_query(query, (question_id,), conn)
        return cursor.rowcount > 0