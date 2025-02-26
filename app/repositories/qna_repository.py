# app/repositories/qna_repository.py
import logging
from typing import List, Optional, Dict, Any
from app.models.qna import QuestionWithAnswers, QuestionWithCategory
from app.models.question import Question
from app.models.answer import Answer
from app.models.category import Category
from app.core.database import get_mysql_connection

logger = logging.getLogger(__name__)


class QnARepository:
    @staticmethod
    async def get_question_with_answers(question_id: int) -> Optional[QuestionWithAnswers]:
        """질문과 그에 대한 답변들을 함께 조회"""
        query = """
        SELECT 
            q.*,
            a.answer_id,
            a.question_id as answer_question_id,
            a.is_correct,
            a.answer_text,
            a.note as answer_note,
            a.create_at as answer_create_at,
            a.update_at as answer_update_at,
            c.category_id,
            c.name as category_name,
            c.is_use as category_is_use,
            c.create_at as category_create_at,
            c.update_at as category_update_at
        FROM 
            question q
        JOIN
            category c ON q.category_id = c.category_id    
        LEFT JOIN 
            answer a ON q.question_id = a.question_id
        WHERE 
            q.question_id = %s
        """

        pool = await get_mysql_connection()
        async with pool as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (question_id,))
                rows = await cursor.fetchall()

                if not rows:
                    return None

                # 첫 번째 행에서 질문 정보 추출
                question_data = {k: v for k, v in rows[0].items()
                                 if not k.startswith('answer_') and not k.startswith('category_')}
                question = Question(**question_data)

                # 카테고리 정보 추출
                category_data = {
                    'category_id': rows[0]['category_id'],
                    'name': rows[0]['category_name'],
                    'is_use': rows[0]['category_is_use'],
                    'create_at': rows[0]['category_create_at'],
                    'update_at': rows[0]['category_update_at']
                }
                category = Category(**category_data)

                # 답변 목록 생성
                answers = []
                for row in rows:
                    if row.get('answer_id'):  # 답변이 있는 경우에만
                        answer_data = {
                            'answer_id': row['answer_id'],
                            'question_id': row['answer_question_id'],
                            'is_correct': row['is_correct'],
                            'answer_text': row['answer_text'],
                            'note': row['answer_note'],
                            'create_at': row['answer_create_at'],
                            'update_at': row['answer_update_at']
                        }
                        answers.append(Answer(**answer_data))

                # 질문, 카테고리, 답변을 합쳐서 반환
                return QuestionWithAnswers(**question.dict(), answers=answers, category=category)

    @staticmethod
    async def get_all_questions_with_answers(
            skip: int = 0,
            limit: int = 10,
            category_id: Optional[int] = None
    ) -> List[QuestionWithAnswers]:
        """모든 질문과 그에 대한 답변들을 함께 조회 (페이지네이션)"""
        # 기본 쿼리
        query = """
        SELECT 
            q.question_id
        FROM 
            question q
        """

        params = []

        # 카테고리 필터링
        if category_id:
            query += " WHERE q.category_id = %s"
            params.append(category_id)

        # 정렬 및 페이지네이션
        query += " ORDER BY q.question_id DESC LIMIT %s, %s"
        params.extend([skip, limit])

        pool = await get_mysql_connection()
        async with pool as conn:
            # 먼저 페이지에 해당하는 질문 ID들 가져오기
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                question_ids = [row['question_id'] for row in await cursor.fetchall()]

            # 각 질문에 대해 상세 정보와 답변 가져오기
            results = []
            for qid in question_ids:
                question_with_answers = await QnARepository.get_question_with_answers(qid)
                if question_with_answers:
                    results.append(question_with_answers)

            return results

    @staticmethod
    async def check_answers(question_id: int, selected_answer_ids: List[int]) -> Dict[str, Any]:
        """사용자가 선택한 답변이 정답인지 확인"""
        # 문제와 답변 정보 가져오기
        query_question = "SELECT * FROM question WHERE question_id = %s"
        query_answers = """
        SELECT answer_id, is_correct
        FROM answer
        WHERE question_id = %s
        """

        pool = await get_mysql_connection()
        async with pool as conn:
            # 1. 문제 정보 조회
            async with conn.cursor() as cursor:
                await cursor.execute(query_question, (question_id,))
                question_data = await cursor.fetchone()

                if not question_data:
                    return {
                        "success": False,
                        "message": "질문을 찾을 수 없습니다.",
                        "is_correct": False,
                        "correct_answers": [],
                        "incorrect_selections": []
                    }

                answer_type = question_data['answer_type']

            # 2. 답변 정보 조회
            async with conn.cursor() as cursor:
                await cursor.execute(query_answers, (question_id,))
                answers = await cursor.fetchall()

                if not answers:
                    return {
                        "success": False,
                        "message": "질문에 대한 답변이 없습니다.",
                        "is_correct": False,
                        "correct_answers": [],
                        "incorrect_selections": []
                    }

                # 정답 ID 리스트
                correct_answer_ids = [a['answer_id'] for a in answers if a['is_correct'] == 'Y']

                # 사용자가 선택한 답변 중 정답이 아닌 것들
                incorrect_selections = [aid for aid in selected_answer_ids if aid not in correct_answer_ids]

                # 사용자가 선택하지 않은 정답들
                unselected_correct = [aid for aid in correct_answer_ids if aid not in selected_answer_ids]

                # 문제 유형에 따른 정답 처리
                is_correct = False

                if answer_type == 1:  # 정답이 한 개인 경우
                    # 정확히 하나의 정답만 선택해야 함
                    is_correct = len(selected_answer_ids) == 1 and len(incorrect_selections) == 0
                else:  # 정답이 여러 개인 경우 (answer_type == 2)
                    # 모든 정답을 선택하고, 오답은 선택하지 않아야 함
                    is_correct = len(unselected_correct) == 0 and len(incorrect_selections) == 0

                message = "정답입니다! 🎉" if is_correct else "오답입니다. 다시 시도해보세요."

                # 정답 설명 추가
                if not is_correct:
                    if answer_type == 1 and len(selected_answer_ids) > 1:
                        message += " 이 문제는 하나의 정답만 선택해야 합니다."
                    elif answer_type == 2 and unselected_correct:
                        message += f" 선택하지 않은 정답이 {len(unselected_correct)}개 있습니다."

                return {
                    "success": True,
                    "message": message,
                    "is_correct": is_correct,
                    "correct_answers": correct_answer_ids,
                    "incorrect_selections": incorrect_selections,
                    "unselected_correct": unselected_correct if not is_correct else []
                }