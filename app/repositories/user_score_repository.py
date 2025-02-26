# app/repositories/user_score_repository.py
import logging
from typing import List, Optional, Dict, Any

from asyncmy import Connection

from app.models.user_score import UserScore, UserScoreCreate, UserCategoryStat
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserScoreRepository(BaseRepository[UserScore]):
    """사용자 성적 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "user_score"
    model_class = UserScore
    id_column = "score_id"

    @classmethod
    async def create_score(cls, score: UserScoreCreate, conn: Connection = None) -> int:
        """새 성적 기록 생성"""
        query = """
        INSERT INTO user_score (user_id, question_id, is_correct, selected_answers)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            score.user_id,
            score.question_id,
            score.is_correct,
            score.selected_answers
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_user_scores(cls, user_id: int, limit: int = 100, conn: Connection = None) -> List[UserScore]:
        """사용자의 성적 기록 조회"""
        query = """
        SELECT * FROM user_score 
        WHERE user_id = %s
        ORDER BY submit_at DESC
        LIMIT %s
        """

        cursor = await cls.execute_query(query, (user_id, limit), conn)
        results = await cursor.fetchall()

        return [UserScore(**result) for result in results]

    @classmethod
    async def get_user_question_score(cls, user_id: int, question_id: int, conn: Connection = None) -> Optional[
        UserScore]:
        """사용자의 특정 문제에 대한 성적 기록 조회"""
        query = """
        SELECT * FROM user_score 
        WHERE user_id = %s AND question_id = %s
        ORDER BY submit_at DESC
        LIMIT 1
        """

        cursor = await cls.execute_query(query, (user_id, question_id), conn)
        result = await cursor.fetchone()

        return UserScore(**result) if result else None

    @classmethod
    async def get_user_score_summary(cls, user_id: int, conn: Connection = None) -> Dict[str, Any]:
        """사용자의 성적 요약 정보 조회"""
        query = """
        SELECT 
            COUNT(*) as total_questions,
            SUM(CASE WHEN is_correct = 'Y' THEN 1 ELSE 0 END) as correct_answers
        FROM 
            user_score
        WHERE 
            user_id = %s
        """

        cursor = await cls.execute_query(query, (user_id,), conn)
        result = await cursor.fetchone()

        return {
            "total_questions": result["total_questions"] if result else 0,
            "correct_answers": result["correct_answers"] if result else 0,
            "accuracy_rate": (result["correct_answers"] / result["total_questions"] * 100)
            if result and result["total_questions"] > 0 else 0
        }


class UserCategoryStatRepository(BaseRepository[UserCategoryStat]):
    """사용자의 카테고리별 성적 통계 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "user_category_stat"
    model_class = UserCategoryStat
    id_column = "stat_id"

    @classmethod
    async def update_category_stat(cls,
                                   user_id: int,
                                   category_id: int,
                                   is_correct: str,
                                   conn: Connection = None) -> None:
        """사용자의 카테고리별 성적 통계 업데이트"""
        # 먼저 해당 사용자의 카테고리 통계가 있는지 확인
        query_check = """
        SELECT * FROM user_category_stat
        WHERE user_id = %s AND category_id = %s
        """

        cursor = await cls.execute_query(query_check, (user_id, category_id), conn)
        existing_stat = await cursor.fetchone()

        if existing_stat:
            # 통계 업데이트
            query_update = """
            UPDATE user_category_stat
            SET 
                total_questions = total_questions + 1,
                correct_answers = correct_answers + %s,
                last_access = CURRENT_TIMESTAMP
            WHERE 
                user_id = %s AND category_id = %s
            """

            correct_value = 1 if is_correct == 'Y' else 0
            await cls.execute_query(query_update, (correct_value, user_id, category_id), conn)
        else:
            # 새 통계 생성
            query_insert = """
            INSERT INTO user_category_stat 
                (user_id, category_id, total_questions, correct_answers)
            VALUES 
                (%s, %s, 1, %s)
            """

            correct_value = 1 if is_correct == 'Y' else 0
            await cls.execute_query(query_insert, (user_id, category_id, correct_value), conn)

    @classmethod
    async def get_user_category_stats(cls, user_id: int, conn: Connection = None) -> List[UserCategoryStat]:
        """사용자의 카테고리별 성적 통계 조회"""
        query = """
        SELECT * FROM user_category_stat
        WHERE user_id = %s
        ORDER BY total_questions DESC, category_id ASC
        """

        cursor = await cls.execute_query(query, (user_id,), conn)
        results = await cursor.fetchall()

        return [UserCategoryStat(**result) for result in results]