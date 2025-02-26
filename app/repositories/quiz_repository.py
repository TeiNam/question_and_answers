# app/repositories/quiz_repository.py
import logging
from typing import List, Optional, Dict, Any
from asyncmy import Connection
from app.models.quiz_session import (
    QuizSession, QuizSessionCreate, QuizSessionWithStats,
    SessionQuestion, SessionQuestionCreate
)
from app.repositories.base_repository import BaseRepository
from app.models.category import Category

logger = logging.getLogger(__name__)


class QuizSessionRepository(BaseRepository[QuizSession]):
    """퀴즈 세션 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "quiz_session"
    model_class = QuizSession
    id_column = "session_id"

    @classmethod
    async def create_session(cls, session: QuizSessionCreate, conn: Connection = None) -> int:
        """새 퀴즈 세션 생성"""
        query = """
        INSERT INTO quiz_session (category_id, name, description)
        VALUES (%s, %s, %s)
        """
        values = (
            session.category_id,
            session.name,
            session.description
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_session_with_stats(cls, session_id: int, conn: Connection = None) -> Optional[QuizSessionWithStats]:
        """세션 정보와 통계 함께 조회"""
        query = """
        SELECT 
            qs.*,
            c.name as category_name,
            c.is_use as category_is_use,
            c.create_at as category_create_at,
            c.update_at as category_update_at,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id) as question_count,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id AND is_answered = 'Y') as completed_count,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id AND is_correct = 'Y') as correct_count
        FROM 
            quiz_session qs
        JOIN
            category c ON qs.category_id = c.category_id
        WHERE 
            qs.session_id = %s
        """

        cursor = await cls.execute_query(query, (session_id,), conn)
        result = await cursor.fetchone()

        if not result:
            return None

        # 카테고리 정보 추출
        category_data = {
            'category_id': result['category_id'],
            'name': result['category_name'],
            'is_use': result['category_is_use'],
            'create_at': result['category_create_at'],
            'update_at': result['category_update_at']
        }
        category = Category(**category_data)

        # 세션 기본 정보 추출
        session_data = {
            'session_id': result['session_id'],
            'category_id': result['category_id'],
            'name': result['name'],
            'description': result['description'],
            'create_at': result['create_at'],
            'update_at': result['update_at'],
            'question_count': result['question_count'],
            'completed_count': result['completed_count'],
            'correct_count': result['correct_count'],
            'category': category
        }

        return QuizSessionWithStats(**session_data)

    @classmethod
    async def get_sessions_by_category(cls, category_id: int, conn: Connection = None) -> List[QuizSessionWithStats]:
        """카테고리별 세션 목록 조회"""
        query = """
        SELECT 
            qs.*,
            c.name as category_name,
            c.is_use as category_is_use,
            c.create_at as category_create_at,
            c.update_at as category_update_at,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id) as question_count,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id AND is_answered = 'Y') as completed_count,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id AND is_correct = 'Y') as correct_count
        FROM 
            quiz_session qs
        JOIN
            category c ON qs.category_id = c.category_id
        WHERE 
            qs.category_id = %s
        ORDER BY 
            qs.create_at DESC
        """

        cursor = await cls.execute_query(query, (category_id,), conn)
        results = await cursor.fetchall()

        sessions = []
        for result in results:
            # 카테고리 정보 추출
            category_data = {
                'category_id': result['category_id'],
                'name': result['category_name'],
                'is_use': result['category_is_use'],
                'create_at': result['category_create_at'],
                'update_at': result['category_update_at']
            }
            category = Category(**category_data)

            # 세션 기본 정보 추출
            session_data = {
                'session_id': result['session_id'],
                'category_id': result['category_id'],
                'name': result['name'],
                'description': result['description'],
                'create_at': result['create_at'],
                'update_at': result['update_at'],
                'question_count': result['question_count'],
                'completed_count': result['completed_count'],
                'correct_count': result['correct_count'],
                'category': category
            }

            sessions.append(QuizSessionWithStats(**session_data))

        return sessions

    @classmethod
    async def get_user_sessions(cls, user_id: int, conn: Connection = None) -> List[QuizSessionWithStats]:
        """사용자의 세션 목록 조회"""
        query = """
        SELECT 
            qs.*,
            c.name as category_name,
            c.is_use as category_is_use,
            c.create_at as category_create_at,
            c.update_at as category_update_at,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id) as question_count,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id AND is_answered = 'Y') as completed_count,
            (SELECT COUNT(*) FROM session_question WHERE session_id = qs.session_id AND is_correct = 'Y') as correct_count
        FROM 
            quiz_session qs
        JOIN
            category c ON qs.category_id = c.category_id
        WHERE 
            qs.session_id IN (
                SELECT DISTINCT sq.session_id 
                FROM session_question sq 
                JOIN user_score us ON sq.question_id = us.question_id 
                WHERE us.user_id = %s
            )
        ORDER BY 
            qs.create_at DESC
        """

        cursor = await cls.execute_query(query, (user_id,), conn)
        results = await cursor.fetchall()

        sessions = []
        for result in results:
            # 카테고리 정보 추출
            category_data = {
                'category_id': result['category_id'],
                'name': result['category_name'],
                'is_use': result['category_is_use'],
                'create_at': result['category_create_at'],
                'update_at': result['category_update_at']
            }
            category = Category(**category_data)

            # 세션 기본 정보 추출
            session_data = {
                'session_id': result['session_id'],
                'category_id': result['category_id'],
                'name': result['name'],
                'description': result['description'],
                'create_at': result['create_at'],
                'update_at': result['update_at'],
                'question_count': result['question_count'],
                'completed_count': result['completed_count'],
                'correct_count': result['correct_count'],
                'category': category
            }

            sessions.append(QuizSessionWithStats(**session_data))

        return sessions


class SessionQuestionRepository(BaseRepository[SessionQuestion]):
    """세션 문제 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "session_question"
    model_class = SessionQuestion
    id_column = "sq_id"

    @classmethod
    async def add_question_to_session(cls,
                                      session_id: int,
                                      question_id: int,
                                      order_num: int,
                                      conn: Connection = None) -> int:
        """세션에 문제 추가"""
        query = """
        INSERT INTO session_question (session_id, question_id, order_num)
        VALUES (%s, %s, %s)
        """
        values = (session_id, question_id, order_num)

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_session_questions(cls, session_id: int, conn: Connection = None) -> List[Dict[str, Any]]:
        """세션에 포함된 문제 ID 목록 조회"""
        query = """
        SELECT sq.*, q.question_text, q.answer_type
        FROM session_question sq
        JOIN question q ON sq.question_id = q.question_id
        WHERE sq.session_id = %s
        ORDER BY sq.order_num
        """

        cursor = await cls.execute_query(query, (session_id,), conn)
        results = await cursor.fetchall()

        return results

    @classmethod
    async def is_question_in_session(cls, session_id: int, question_id: int, conn: Connection = None) -> bool:
        """문제가 해당 세션에 있는지 확인"""
        query = """
        SELECT COUNT(*) as count
        FROM session_question
        WHERE session_id = %s AND question_id = %s
        """

        cursor = await cls.execute_query(query, (session_id, question_id), conn)
        result = await cursor.fetchone()

        return result["count"] > 0

    @classmethod
    async def update_question_result(cls,
                                     session_id: int,
                                     question_id: int,
                                     is_correct: str,
                                     conn: Connection = None) -> bool:
        """세션 문제의 결과 업데이트"""
        query = """
        UPDATE session_question
        SET is_answered = 'Y', is_correct = %s, answer_time = CURRENT_TIMESTAMP
        WHERE session_id = %s AND question_id = %s
        """

        cursor = await cls.execute_query(query, (is_correct, session_id, question_id), conn)
        return cursor.rowcount > 0