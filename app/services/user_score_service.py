# app/services/user_score_service.py
import logging
from typing import List, Dict, Any

from app.core.database import transaction
from app.core.exceptions import NotFoundException, DatabaseException
from app.models.submit import SubmitAnswer
from app.models.user_score import UserScore, UserScoreCreate, UserScoreSummary
from app.repositories.qna_repository import QnARepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.user_score_repository import UserScoreRepository, UserCategoryStatRepository

logger = logging.getLogger(__name__)


class UserScoreService:
    @staticmethod
    async def record_user_answer(
            user_id: int,
            submit_data: SubmitAnswer
    ) -> Dict[str, Any]:
        """사용자 답변 제출 기록 및 채점"""
        try:
            # 질문 존재 여부 확인
            question = await QuestionRepository.get_by_id(submit_data.question_id)
            if not question:
                raise NotFoundException(f"ID가 {submit_data.question_id}인 질문을 찾을 수 없습니다.")

            # 정답 확인
            answer_result = await QnARepository.check_answers(
                submit_data.question_id,
                submit_data.selected_answer_ids
            )

            async with transaction() as conn:
                # 사용자 성적 기록 생성
                score_data = UserScoreCreate(
                    user_id=user_id,
                    question_id=submit_data.question_id,
                    is_correct="Y" if answer_result["is_correct"] else "N",
                    selected_answers=",".join(map(str, submit_data.selected_answer_ids))
                )

                score_id = await UserScoreRepository.create_score(score_data, conn)

                # 카테고리 통계 업데이트
                await UserCategoryStatRepository.update_category_stat(
                    user_id,
                    question.category_id,
                    score_data.is_correct,
                    conn
                )

            # 로그 기록
            logger.info(
                f"사용자 답변 기록 (사용자 ID: {user_id}, 질문 ID: {submit_data.question_id}, 정답 여부: {score_data.is_correct})")

            # 결과에 성적 ID 추가
            answer_result["score_id"] = score_id

            return answer_result

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"사용자 답변 기록 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_user_scores(user_id: int, limit: int = 100) -> List[UserScore]:
        """사용자의 성적 기록 조회"""
        try:
            return await UserScoreRepository.get_user_scores(user_id, limit)
        except Exception as e:
            logger.error(f"사용자 성적 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_user_score_summary(user_id: int) -> UserScoreSummary:
        """사용자의 성적 요약 정보 조회"""
        try:
            # 전체 요약 정보
            summary = await UserScoreRepository.get_user_score_summary(user_id)

            # 카테고리별 통계
            category_stats = await UserCategoryStatRepository.get_user_category_stats(user_id)

            return UserScoreSummary(
                total_questions=summary["total_questions"],
                correct_answers=summary["correct_answers"],
                accuracy_rate=summary["accuracy_rate"],
                category_stats=category_stats
            )
        except Exception as e:
            logger.error(f"사용자 성적 요약 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))