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
        INSERT INTO question (category_id, user_id, answer_type, question_text, note, link_url, group_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            question.category_id,
            question.user_id,
            question.answer_type,
            question.question_text,
            question.note,
            question.link_url,
            question.group_id
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_all_by_creator(cls,
                                 user_id: int,
                                 skip: int = 0,
                                 limit: int = 100,
                                 conn: Connection = None) -> List[Question]:
        """출제자 ID로 질문 목록 조회"""
        where_clause = "user_id = %s"
        params = (user_id,)

        return await cls.get_all(
            where_clause=where_clause,
            params=params,
            order_by="question_id DESC",
            limit=limit,
            offset=skip,
            conn=conn
        )

    @classmethod
    async def get_questions_by_group(cls,
                                     group_id: int,
                                     skip: int = 0,
                                     limit: int = 100,
                                     conn: Connection = None) -> List[Question]:
        """그룹 ID로 질문 목록 조회"""
        where_clause = "group_id = %s"
        params = (group_id,)

        return await cls.get_all(
            where_clause=where_clause,
            params=params,
            order_by="question_id DESC",
            limit=limit,
            offset=skip,
            conn=conn
        )

    @classmethod
    async def get_available_questions_for_user(cls,
                                               user_id: int,
                                               skip: int = 0,
                                               limit: int = 100,
                                               category_id: Optional[int] = None,
                                               conn: Connection = None) -> List[Question]:
        """사용자가 풀 수 있는 질문 목록 조회"""
        query = """
        SELECT q.* FROM question q
        WHERE (q.group_id IS NULL OR q.group_id IN (
            SELECT group_id FROM group_member WHERE user_id = %s
        ))
        """

        params = [user_id]

        if category_id:
            query += " AND q.category_id = %s"
            params.append(category_id)

        query += " ORDER BY q.question_id DESC LIMIT %s, %s"
        params.extend([skip, limit])

        cursor = await cls.execute_query(query, tuple(params), conn)
        results = await cursor.fetchall()

        return [Question(**result) for result in results]

    @classmethod
    async def update(cls, question_id: int, question_update: QuestionUpdate, conn: Connection = None) -> bool:
        """질문 업데이트"""
        return await super().update(question_id, question_update, conn)