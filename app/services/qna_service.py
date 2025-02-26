# app/services/qna_service.py
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.models.question import Question, QuestionCreate, QuestionUpdate
from app.models.answer import Answer, AnswerCreate, AnswerUpdate
from app.models.category import Category, CategoryCreate, CategoryUpdate
from app.models.qna import QuestionWithAnswers
from app.repositories.question_repository import QuestionRepository
from app.repositories.answer_repository import AnswerRepository
from app.repositories.qna_repository import QnARepository
from app.repositories.category_repository import CategoryRepository
from app.core.database import get_mysql_connection

logger = logging.getLogger(__name__)


class QnAService:
    @staticmethod
    async def create_question_with_answers(
            question: QuestionCreate,
            answers: List[AnswerCreate]
    ) -> Dict[str, Any]:
        """질문과 답변을 함께 생성"""
        # MySQL 풀에서 연결 가져오기
        try:
            # 카테고리 존재 확인
            category = await CategoryRepository.get_by_id(question.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ID가 {question.category_id}인 카테고리를 찾을 수 없습니다."
                )

            pool = await get_mysql_connection()
            async with pool as conn:
                # 트랜잭션 시작
                await conn.begin()
                try:
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

                    # 트랜잭션 커밋
                    await conn.commit()

                    # 활동 로그 기록
                    logger.info(f"질문 생성 (ID: {question_id}) - 답변 수: {len(answer_ids)}")

                    return {
                        "success": True,
                        "question_id": question_id,
                        "answer_ids": answer_ids,
                        "message": "질문과 답변이 성공적으로 생성되었습니다."
                    }

                except Exception as e:
                    # 오류 발생 시 롤백
                    await conn.rollback()
                    logger.error(f"질문 및 답변 생성 중 오류 발생: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"질문 및 답변 생성 중 오류 발생: {str(e)}"
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"데이터베이스 연결 중 오류 발생: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"데이터베이스 연결 중 오류 발생: {str(e)}"
            )

    @staticmethod
    async def get_question_with_answers(question_id: int) -> QuestionWithAnswers:
        """질문과 해당하는 답변들 조회"""
        result = await QnARepository.get_question_with_answers(question_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {question_id}인 질문을 찾을 수 없습니다."
            )
        return result

    @staticmethod
    async def get_all_questions_with_answers(
            skip: int = 0,
            limit: int = 10,
            category_id: Optional[int] = None
    ) -> List[QuestionWithAnswers]:
        """모든 질문과 답변 조회 (페이지네이션 포함)"""
        # 카테고리 ID가 제공된 경우 카테고리 존재 확인
        if category_id:
            category = await CategoryRepository.get_by_id(category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ID가 {category_id}인 카테고리를 찾을 수 없습니다."
                )

        return await QnARepository.get_all_questions_with_answers(skip, limit, category_id)

    @staticmethod
    async def update_question(
            question_id: int,
            question_update: QuestionUpdate
    ) -> Dict[str, Any]:
        """질문 업데이트"""
        # 질문 존재 여부 확인
        question = await QuestionRepository.get_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {question_id}인 질문을 찾을 수 없습니다."
            )

        # 카테고리 ID가 제공된 경우 카테고리 존재 확인
        if question_update.category_id:
            category = await CategoryRepository.get_by_id(question_update.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"ID가 {question_update.category_id}인 카테고리를 찾을 수 없습니다."
                )

        # 질문 업데이트
        success = await QuestionRepository.update(question_id, question_update)

        # 로그 기록
        logger.info(f"질문 업데이트 (ID: {question_id}) - 필드: {', '.join(question_update.dict(exclude_unset=True).keys())}")

        return {
            "success": success,
            "message": "질문이 성공적으로 업데이트되었습니다."
        }

    @staticmethod
    async def update_answer(
            answer_id: int,
            answer_update: AnswerUpdate
    ) -> Dict[str, Any]:
        """답변 업데이트"""
        # 답변 존재 여부 확인
        answer = await AnswerRepository.get_by_id(answer_id)
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {answer_id}인 답변을 찾을 수 없습니다."
            )

        # 답변 업데이트
        success = await AnswerRepository.update(answer_id, answer_update)

        # 로그 기록
        logger.info(f"답변 업데이트 (ID: {answer_id}) - 필드: {', '.join(answer_update.dict(exclude_unset=True).keys())}")

        return {
            "success": success,
            "message": "답변이 성공적으로 업데이트되었습니다."
        }

    @staticmethod
    async def delete_question(question_id: int) -> Dict[str, Any]:
        """질문 및 관련 답변 삭제"""
        try:
            pool = await get_mysql_connection()
            async with pool as conn:
                # 트랜잭션 시작
                await conn.begin()
                try:
                    # 질문 존재 여부 확인
                    question = await QuestionRepository.get_by_id(question_id, conn)
                    if not question:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"ID가 {question_id}인 질문을 찾을 수 없습니다."
                        )

                    # 관련 답변 삭제
                    await AnswerRepository.delete_by_question_id(question_id, conn)

                    # 질문 삭제
                    success = await QuestionRepository.delete(question_id, conn)

                    # 트랜잭션 커밋
                    await conn.commit()

                    # 로그 기록
                    logger.info(f"질문 삭제 (ID: {question_id})")

                    return {
                        "success": success,
                        "message": "질문 및 관련 답변이 성공적으로 삭제되었습니다."
                    }

                except Exception as e:
                    # 오류 발생 시 롤백
                    await conn.rollback()
                    logger.error(f"질문 및 답변 삭제 중 오류 발생: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"질문 및 답변 삭제 중 오류 발생: {str(e)}"
                    )
        except Exception as e:
            logger.error(f"데이터베이스 연결 중 오류 발생: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"데이터베이스 연결 중 오류 발생: {str(e)}"
            )

    @staticmethod
    async def check_answers(
            question_id: int,
            selected_answer_ids: List[int]
    ) -> Dict[str, Any]:
        """사용자가 선택한 답변이 정답인지 확인"""
        # 질문 존재 여부 확인
        question = await QuestionRepository.get_by_id(question_id)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID가 {question_id}인 질문을 찾을 수 없습니다."
            )

        # 정답 확인
        result = await QnARepository.check_answers(question_id, selected_answer_ids)

        # 로그 기록
        logger.info(f"답변 제출 (질문 ID: {question_id}) - 결과: {'정답' if result.get('is_correct') else '오답'}")

        return result