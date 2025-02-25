# app/repositories/question_repository.py
import logging
from typing import List, Optional
import asyncmy
from app.models.question import Question, QuestionCreate, QuestionUpdate
from app.core.database import get_mysql_connection

logger = logging.getLogger(__name__)


class QuestionRepository:
    @staticmethod
    async def create(question: QuestionCreate, conn=None) -> int:
        """새 질문 생성"""
        query = """
        INSERT INTO question (category, answer_type, question_text, note, link_url)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            question.category,
            question.answer_type,
            question.question_text,
            question.note,
            question.link_url
        )

        if conn:
            # 외부에서 커넥션이 제공된 경우
            async with conn.cursor() as cursor:
                await cursor.execute(query, values)
                return cursor.lastrowid
        else:
            # 커넥션 생성
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, values)
                    return cursor.lastrowid

    @staticmethod
    async def get_by_id(question_id: int, conn=None) -> Optional[Question]:
        """ID로 질문 조회"""
        query = "SELECT * FROM question WHERE question_id = %s"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (question_id,))
                result = await cursor.fetchone()
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (question_id,))
                    result = await cursor.fetchone()

        return Question(**result) if result else None

    @staticmethod
    async def get_all(
            skip: int = 0,
            limit: int = 100,
            category: Optional[str] = None,
            conn=None
    ) -> List[Question]:
        """모든 질문 조회 (페이지네이션 포함, 카테고리별 필터링 지원)"""
        query = "SELECT * FROM question"
        params = []

        # 카테고리 필터링
        if category:
            query += " WHERE category = %s"
            params.append(category)

        # 정렬 및 페이지네이션
        query += " ORDER BY question_id DESC LIMIT %s, %s"
        params.extend([skip, limit])

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                results = await cursor.fetchall()
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    results = await cursor.fetchall()

        return [Question(**result) for result in results]

    @staticmethod
    async def update(
            question_id: int,
            question_update: QuestionUpdate,
            conn=None
    ) -> bool:
        """질문 업데이트"""
        # 업데이트할 필드 구성 (None이 아닌 필드만)
        update_fields = {}
        if question_update.category is not None:
            update_fields["category"] = question_update.category
        if question_update.question_text is not None:
            update_fields["question_text"] = question_update.question_text
        if question_update.answer_type is not None:
            update_fields["answer_type"] = question_update.answer_type
        if question_update.note is not None:
            update_fields["note"] = question_update.note
        if question_update.link_url is not None:
            update_fields["link_url"] = question_update.link_url

        if not update_fields:
            return True  # 업데이트할 필드가 없음

        # 쿼리 구성
        set_clause = ", ".join(f"{field} = %s" for field in update_fields.keys())
        query = f"UPDATE question SET {set_clause} WHERE question_id = %s"

        # 파라미터 구성
        params = list(update_fields.values())
        params.append(question_id)

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.rowcount > 0
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    return cursor.rowcount > 0

    @staticmethod
    async def delete(question_id: int, conn=None) -> bool:
        """질문 삭제"""
        query = "DELETE FROM question WHERE question_id = %s"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (question_id,))
                return cursor.rowcount > 0
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (question_id,))
                    return cursor.rowcount > 0
