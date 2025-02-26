# app/services/quiz_service.py
import logging
from typing import List, Dict, Any

from app.core.database import transaction
from app.core.exceptions import NotFoundException, DatabaseException, ValidationException
from app.models.quiz_session import (
    QuizSessionCreate, QuizSessionWithStats
)
from app.models.submit import SubmitAnswer
from app.repositories.category_repository import CategoryRepository
from app.repositories.qna_repository import QnARepository
from app.repositories.quiz_repository import QuizSessionRepository, SessionQuestionRepository
from app.services.user_score_service import UserScoreService

logger = logging.getLogger(__name__)


class QuizService:
    @staticmethod
    async def create_quiz_session(session: QuizSessionCreate, question_count: int = 10) -> Dict[str, Any]:
        """카테고리 기반으로 퀴즈 세션 생성"""
        try:
            # 카테고리 존재 확인
            category = await CategoryRepository.get_by_id(session.category_id)
            if not category:
                raise NotFoundException(f"ID가 {session.category_id}인 카테고리를 찾을 수 없습니다.")

            async with transaction() as conn:
                # 세션 생성
                session_id = await QuizSessionRepository.create_session(session, conn)

                # 해당 카테고리에서 랜덤하게 문제 가져오기
                questions = await QnARepository.get_all_questions_with_answers(
                    skip=0,
                    limit=question_count,
                    category_id=session.category_id,
                    is_random=True
                )

                # 세션에 문제 추가
                for idx, q in enumerate(questions, start=1):
                    await SessionQuestionRepository.add_question_to_session(
                        session_id,
                        q.question_id,
                        idx,
                        conn
                    )

                # 로그 기록
                logger.info(f"퀴즈 세션 생성: {session_id} (카테고리: {category.name}, 문제 수: {len(questions)})")

                return {
                    "success": True,
                    "session_id": session_id,
                    "question_count": len(questions),
                    "message": f"카테고리 '{category.name}'의 퀴즈 세션이 생성되었습니다."
                }

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"퀴즈 세션 생성 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_quiz_session(session_id: int) -> QuizSessionWithStats:
        """퀴즈 세션 정보 조회"""
        try:
            session = await QuizSessionRepository.get_session_with_stats(session_id)
            if not session:
                raise NotFoundException(f"ID가 {session_id}인 퀴즈 세션을 찾을 수 없습니다.")
            return session
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"퀴즈 세션 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_category_sessions(category_id: int) -> List[QuizSessionWithStats]:
        """카테고리별 퀴즈 세션 목록 조회"""
        try:
            # 카테고리 존재 확인
            category = await CategoryRepository.get_by_id(category_id)
            if not category:
                raise NotFoundException(f"ID가 {category_id}인 카테고리를 찾을 수 없습니다.")

            return await QuizSessionRepository.get_sessions_by_category(category_id)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"카테고리별 세션 목록 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def submit_session_answer(
            session_id: int,
            question_id: int,
            selected_answer_ids: List[int],
            user_id: int
    ) -> Dict[str, Any]:
        """세션 내 문제 답변 제출"""
        try:
            # 세션 존재 확인
            session = await QuizSessionRepository.get_session_with_stats(session_id)
            if not session:
                raise NotFoundException(f"ID가 {session_id}인 퀴즈 세션을 찾을 수 없습니다.")

            # 세션에 문제가 포함되어 있는지 확인
            if not await SessionQuestionRepository.is_question_in_session(session_id, question_id):
                raise ValidationException(f"해당 퀴즈 세션에 ID가 {question_id}인 문제가 없습니다.")

            # 사용자 성적 서비스를 이용해 답변 기록 및 결과 확인
            submit_data = SubmitAnswer(
                question_id=question_id,
                selected_answer_ids=selected_answer_ids
            )
            result = await UserScoreService.record_user_answer(user_id, submit_data)

            # 세션 문제 결과 업데이트
            await SessionQuestionRepository.update_question_result(
                session_id,
                question_id,
                "Y" if result["is_correct"] else "N"
            )

            # 응답에 세션 ID 추가
            result["session_id"] = session_id

            return result
        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"세션 답변 제출 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_session_questions(session_id: int) -> List[Dict[str, Any]]:
        """세션에 포함된 문제 목록 조회"""
        try:
            # 세션 존재 확인
            session = await QuizSessionRepository.get_session_with_stats(session_id)
            if not session:
                raise NotFoundException(f"ID가 {session_id}인 퀴즈 세션을 찾을 수 없습니다.")

            # 세션 문제 목록 조회
            session_questions = await SessionQuestionRepository.get_session_questions(session_id)

            # 문제 상세 정보 조회
            result = []
            for sq in session_questions:
                # 문제 상세 정보를 QnA 레포지토리에서 가져오지만,
                # 이미 답변을 제출한 경우에는 답변 정보를 표시하지 않음
                q_detail = await QnARepository.get_question_with_answers(sq["question_id"])

                # 답변 제출 전인 경우에만 정답 정보 숨김
                if sq["is_answered"] == "N":
                    # 답변에서 is_correct 정보 제거 (정답 숨김)
                    for answer in q_detail.answers:
                        answer.is_correct = "?"

                # 세션 문제 정보와 상세 정보 합치기
                question_data = {
                    "sq_id": sq["sq_id"],
                    "session_id": sq["session_id"],
                    "question_id": sq["question_id"],
                    "order_num": sq["order_num"],
                    "is_answered": sq["is_answered"],
                    "is_correct": sq["is_correct"],
                    "answer_time": sq["answer_time"],
                    "detail": q_detail
                }

                result.append(question_data)

            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"세션 문제 목록 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_user_sessions(user_id: int) -> List[QuizSessionWithStats]:
        """사용자의 퀴즈 세션 목록 조회"""
        try:
            return await QuizSessionRepository.get_user_sessions(user_id)
        except Exception as e:
            logger.error(f"사용자 세션 목록 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))