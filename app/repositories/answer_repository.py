# app/repositories/answer_repository.py
import logging
from typing import List, Optional
import asyncmy
from app.models.answer import Answer, AnswerCreate, AnswerUpdate
from app.core.database import get_mysql_connection

logger = logging.getLogger(__name__)


class AnswerRepository:
    @staticmethod
    async def create(answer: AnswerCreate, conn=None) -> int:
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
    async def get_by_id(answer_id: int, conn=None) -> Optional[Answer]:
        """ID로 답변 조회"""
        query = "SELECT * FROM answer WHERE answer_id = %s"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (answer_id,))
                result = await cursor.fetchone()
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (answer_id,))
                    result = await cursor.fetchone()

        return Answer(**result) if result else None

    @staticmethod
    async def get_by_question_id(question_id: int, conn=None) -> List[Answer]:
        """질문 ID로 답변들 조회"""
        query = "SELECT * FROM answer WHERE question_id = %s"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (question_id,))
                results = await cursor.fetchall()
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (question_id,))
                    results = await cursor.fetchall()

        return [Answer(**result) for result in results]

    @staticmethod
    async def update(
            answer_id: int,
            answer_update: AnswerUpdate,
            conn=None
    ) -> bool:
        """답변 업데이트"""
        # 업데이트할 필드 구성 (None이 아닌 필드만)
        update_fields = {}
        if answer_update.answer_text is not None:
            update_fields["answer_text"] = answer_update.answer_text
        if answer_update.is_correct is not None:
            update_fields["is_correct"] = answer_update.is_correct
        if answer_update.note is not None:
            update_fields["note"] = answer_update.note

        if not update_fields:
            return True  # 업데이트할 필드가 없음

        # 쿼리 구성
        set_clause = ", ".join(f"{field} = %s" for field in update_fields.keys())
        query = f"UPDATE answer SET {set_clause} WHERE answer_id = %s"

        # 파라미터 구성
        params = list(update_fields.values())
        params.append(answer_id)

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
    async def delete(answer_id: int, conn=None) -> bool:
        """답변 삭제"""
        query = "DELETE FROM answer WHERE answer_id = %s"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (answer_id,))
                return cursor.rowcount > 0
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (answer_id,))
                    return cursor.rowcount > 0

    @staticmethod
    async def delete_by_question_id(question_id: int, conn=None) -> bool:
        """질문 ID로 모든 답변 삭제"""
        query = "DELETE FROM answer WHERE question_id = %s"

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