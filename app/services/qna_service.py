# app/services/qna_service.py
import logging
from typing import List, Optional, Dict, Any

from app.core.database import transaction
from app.core.exceptions import NotFoundException, DatabaseException, ForbiddenException
from app.models.answer import AnswerCreate, AnswerUpdate
from app.models.qna import QuestionWithAnswers
from app.models.question import QuestionCreate, QuestionUpdate
from app.repositories.answer_repository import AnswerRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.qna_repository import QnARepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class QnAService:
    @staticmethod
    async def create_question_with_answers(
            question: QuestionCreate,
            answers: List[AnswerCreate]
    ) -> Dict[str, Any]:
        """질문과 답변을 함께 생성"""
        try:
            # 카테고리 존재 확인
            category = await CategoryRepository.get_by_id(question.category_id)
            if not category:
                raise NotFoundException(f"ID가 {question.category_id}인 카테고리를 찾을 수 없습니다.")

            # 출제자 권한 확인
            user = await UserRepository.get_by_id(question.user_id)
            if not user:
                raise NotFoundException(f"ID가 {question.user_id}인 사용자를 찾을 수 없습니다.")

            if user.role != "creator" and user.role != "admin":
                raise ForbiddenException("문제 생성 권한이 없습니다. 출제자 또는 관리자만 문제를 생성할 수 있습니다.")

            # 그룹 ID가 제공된 경우 존재 확인
            if question.group_id:
                group = await GroupRepository.get_by_id(question.group_id)
                if not group:
                    raise NotFoundException(f"ID가 {question.group_id}인 그룹을 찾을 수 없습니다.")

                # 그룹 소유자인지 확인
                if group.user_id != question.user_id and user.role != "admin":
                    raise ForbiddenException("해당 그룹에 문제를 생성할 권한이 없습니다.")

            async with transaction() as conn:
                # 질문 생성
                question_id = await QuestionRepository.create(question, conn)

                # 답변 목록 생성
                answer_ids = []
                for answer in answers:
                    # 질문 ID 설정
                    answer.question_id = question_id
                    # 답변 생성
                    answer_id = await AnswerRepository.create(answer, conn)
                    answer_ids.append(answer_id)

                # 로그 기록
                logger.info(f"질문 생성 (ID: {question_id}) - 출제자: {question.user_id}, 답변 수: {len(answer_ids)}")

                return {
                    "success": True,
                    "question_id": question_id,
                    "answer_ids": answer_ids,
                    "message": "질문과 답변이 성공적으로 생성되었습니다."
                }

        except (NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"질문 및 답변 생성 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_question_with_answers(question_id: int) -> QuestionWithAnswers:
        """질문과 해당하는 답변들 조회"""
        result = await QnARepository.get_question_with_answers(question_id)
        if not result:
            raise NotFoundException(f"ID가 {question_id}인 질문을 찾을 수 없습니다.")
        return result

    @staticmethod
    async def get_all_questions_with_answers(
            skip: int = 0,
            limit: int = 10,
            category_id: Optional[int] = None,
            user_id: int = None,
            is_random: bool = False
    ) -> List[QuestionWithAnswers]:
        """모든 질문과 답변 조회 (페이지네이션 포함)"""
        try:
            # 카테고리 ID가 제공된 경우 카테고리 존재 확인
            if category_id:
                category = await CategoryRepository.get_by_id(category_id)
                if not category:
                    raise NotFoundException(f"ID가 {category_id}인 카테고리를 찾을 수 없습니다.")

            # 사용자 정보 확인
            user = None
            if user_id:
                user = await UserRepository.get_by_id(user_id)
                if not user:
                    raise NotFoundException(f"ID가 {user_id}인 사용자를 찾을 수 없습니다.")

            # 사용자 권한에 따라 조회할 질문 결정
            if user and user.role in ["creator", "admin"]:
                # 출제자나 관리자는 모든 질문 조회 가능
                return await QnARepository.get_all_questions_with_answers(skip, limit, category_id, is_random)
            elif user:
                # 풀이자는 자신이 속한 그룹의 질문 또는 그룹 제한이 없는 질문만 조회 가능
                questions = await QuestionRepository.get_available_questions_for_user(user_id, skip, limit, category_id)

                # 각 질문에 대한 상세 정보 조회
                results = []
                for q in questions:
                    question_with_answers = await QnARepository.get_question_with_answers(q.question_id)
                    if question_with_answers:
                        results.append(question_with_answers)

                return results
            else:
                # 사용자 정보가 없으면 그룹 제한이 없는 질문만 조회
                return await QnARepository.get_all_questions_with_answers(skip, limit, category_id, is_random)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"질문 목록 조회 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def update_question(
            question_id: int,
            question_update: QuestionUpdate
    ) -> Dict[str, Any]:
        """질문 업데이트"""
        try:
            # 질문 존재 여부 확인
            question = await QuestionRepository.get_by_id(question_id)
            if not question:
                raise NotFoundException(f"ID가 {question_id}인 질문을 찾을 수 없습니다.")

            # 카테고리 ID가 제공된 경우 카테고리 존재 확인
            if question_update.category_id:
                category = await CategoryRepository.get_by_id(question_update.category_id)
                if not category:
                    raise NotFoundException(f"ID가 {question_update.category_id}인 카테고리를 찾을 수 없습니다.")

            # 질문 업데이트
            success = await QuestionRepository.update(question_id, question_update)

            # 로그 기록
            update_fields = ', '.join(k for k, v in question_update.dict(exclude_unset=True).items() if v is not None)
            logger.info(f"질문 업데이트 (ID: {question_id}) - 필드: {update_fields}")

            return {
                "success": success,
                "message": "질문이 성공적으로 업데이트되었습니다."
            }
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"질문 업데이트 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def update_answer(
            answer_id: int,
            answer_update: AnswerUpdate
    ) -> Dict[str, Any]:
        """답변 업데이트"""
        try:
            # 답변 존재 여부 확인
            answer = await AnswerRepository.get_by_id(answer_id)
            if not answer:
                raise NotFoundException(f"ID가 {answer_id}인 답변을 찾을 수 없습니다.")

            # 답변 업데이트
            success = await AnswerRepository.update(answer_id, answer_update)

            # 로그 기록
            update_fields = ', '.join(k for k, v in answer_update.dict(exclude_unset=True).items() if v is not None)
            logger.info(f"답변 업데이트 (ID: {answer_id}) - 필드: {update_fields}")

            return {
                "success": success,
                "message": "답변이 성공적으로 업데이트되었습니다."
            }
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"답변 업데이트 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def delete_question(question_id: int) -> Dict[str, Any]:
        """질문 및 관련 답변 삭제"""
        try:
            async with transaction() as conn:
                # 질문 존재 여부 확인
                question = await QuestionRepository.get_by_id(question_id, conn)
                if not question:
                    raise NotFoundException(f"ID가 {question_id}인 질문을 찾을 수 없습니다.")

                # 관련 답변 삭제
                await AnswerRepository.delete_by_question_id(question_id, conn)

                # 질문 삭제
                success = await QuestionRepository.delete(question_id, conn)

                # 로그 기록
                logger.info(f"질문 삭제 (ID: {question_id})")

                return {
                    "success": success,
                    "message": "질문 및 관련 답변이 성공적으로 삭제되었습니다."
                }
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"질문 삭제 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def check_answers(
            question_id: int,
            selected_answer_ids: List[int]
    ) -> Dict[str, Any]:
        """사용자가 선택한 답변이 정답인지 확인"""
        try:
            # 질문 존재 여부 확인
            question = await QuestionRepository.get_by_id(question_id)
            if not question:
                raise NotFoundException(f"ID가 {question_id}인 질문을 찾을 수 없습니다.")

            # 정답 확인
            result = await QnARepository.check_answers(question_id, selected_answer_ids)

            # 로그 기록
            logger.info(f"답변 제출 (질문 ID: {question_id}) - 결과: {'정답' if result.get('is_correct') else '오답'}")

            return result
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"답변 확인 중 오류 발생: {e}")
            raise DatabaseException(str(e))
