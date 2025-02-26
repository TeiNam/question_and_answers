# tests/test_qna_api.py
import pytest
from httpx import AsyncClient
from typing import Dict, List, Any
from fastapi import FastAPI
import asyncio
from main import app
import json

# 테스트용 카테고리 데이터
TEST_CATEGORY = {
    "name": "프로그래밍",
    "is_use": "Y"
}

# 테스트용 질문 데이터
TEST_QUESTION = {
    "category_id": 0,  # 테스트 실행 시 실제 카테고리 ID로 교체됨
    "question_text": "Python에서 비동기 프로그래밍을 위해 사용하는 키워드는?",
    "answer_type": 1,
    "note": "Python 3.5부터 도입되었습니다.",
    "link_url": "https://docs.python.org/3/library/asyncio.html"
}

# 테스트용 답변 데이터
TEST_ANSWERS = [
    {"question_id": 0, "answer_text": "async/await", "is_correct": "Y", "note": "정답입니다."},
    {"question_id": 0, "answer_text": "yield/return", "is_correct": "N", "note": "Generator에 사용되는 키워드입니다."},
    {"question_id": 0, "answer_text": "try/except", "is_correct": "N", "note": "예외 처리에 사용되는 키워드입니다."},
    {"question_id": 0, "answer_text": "if/else", "is_correct": "N", "note": "조건문에 사용되는 키워드입니다."}
]


@pytest.fixture
async def test_client():
    """테스트 클라이언트 설정"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="module")
def event_loop():
    """pytest에서 asyncio 이벤트 루프 생성"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_category(test_client: AsyncClient) -> Dict[str, Any]:
    """테스트용 카테고리 생성"""
    response = await test_client.post(
        "/api/v1/categories/",
        json=TEST_CATEGORY
    )

    assert response.status_code == 201
    data = response.json()
    return data


@pytest.mark.asyncio
async def test_category_crud(test_client: AsyncClient) -> None:
    """카테고리 CRUD 테스트"""
    # 카테고리 생성
    response = await test_client.post(
        "/api/v1/categories/",
        json=TEST_CATEGORY
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "category_id" in data

    category_id = data["category_id"]

    # 카테고리 조회
    response = await test_client.get(f"/api/v1/categories/{category_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["category_id"] == category_id
    assert data["name"] == TEST_CATEGORY["name"]

    # 카테고리 업데이트
    update_data = {
        "name": "파이썬 프로그래밍"
    }

    response = await test_client.put(
        f"/api/v1/categories/{category_id}",
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # 업데이트 확인
    response = await test_client.get(f"/api/v1/categories/{category_id}")
    data = response.json()
    assert data["name"] == update_data["name"]

    # 카테고리 삭제는 참조 무결성 때문에 테스트하지 않음


@pytest.mark.asyncio
async def test_create_and_get_question(test_client: AsyncClient, test_category: Dict[str, Any]) -> None:
    """문제 생성 및 조회 테스트"""
    # 카테고리 ID 설정
    category_id = test_category["category_id"]
    question = TEST_QUESTION.copy()
    question["category_id"] = category_id

    # 문제 생성 요청
    response = await test_client.post(
        "/api/v1/qna/questions",
        json={
            "question": question,
            "answers": TEST_ANSWERS
        }
    )

    # 응답 상태 코드 확인
    assert response.status_code == 201

    # 응답 데이터 파싱
    data = response.json()
    assert data["success"] is True
    assert "question_id" in data
    assert "answer_ids" in data

    # 생성된 문제 ID 가져오기
    question_id = data["question_id"]

    # 문제 조회 요청
    response = await test_client.get(f"/api/v1/qna/questions/{question_id}")

    # 응답 상태 코드 확인
    assert response.status_code == 200

    # 응답 데이터 확인
    data = response.json()
    assert data["question_id"] == question_id
    assert data["category_id"] == category_id
    assert data["question_text"] == question["question_text"]
    assert len(data["answers"]) == len(TEST_ANSWERS)
    assert "category" in data
    assert data["category"]["category_id"] == category_id


@pytest.mark.asyncio
async def test_submit_answers(test_client: AsyncClient, test_category: Dict[str, Any]) -> None:
    """답변 제출 테스트"""
    # 카테고리 ID 설정
    category_id = test_category["category_id"]
    question = TEST_QUESTION.copy()
    question["category_id"] = category_id

    # 테스트용 문제 생성
    response = await test_client.post(
        "/api/v1/qna/questions",
        json={
            "question": question,
            "answers": TEST_ANSWERS
        }
    )

    # 문제 ID 및 정답 ID 가져오기
    data = response.json()
    question_id = data["question_id"]
    answer_ids = data["answer_ids"]

    # 정답 제출 (첫 번째 답변이 정답)
    response = await test_client.post(
        "/api/v1/qna/submit",
        json={
            "question_id": question_id,
            "selected_answer_ids": [answer_ids[0]]
        }
    )

    # 응답 상태 코드 확인
    assert response.status_code == 200

    # 정답 여부 확인
    data = response.json()
    assert data["success"] is True
    assert data["is_correct"] is True
    assert len(data["incorrect_selections"]) == 0

    # 오답 제출 (두 번째 답변은 오답)
    response = await test_client.post(
        "/api/v1/qna/submit",
        json={
            "question_id": question_id,
            "selected_answer_ids": [answer_ids[1]]
        }
    )

    # 응답 상태 코드 확인
    assert response.status_code == 200

    # 정답 여부 확인
    data = response.json()
    assert data["success"] is True
    assert data["is_correct"] is False
    assert len(data["incorrect_selections"]) == 1


@pytest.mark.asyncio
async def test_update_question(test_client: AsyncClient, test_category: Dict[str, Any]) -> None:
    """문제 업데이트 테스트"""
    # 카테고리 ID 설정
    category_id = test_category["category_id"]
    question = TEST_QUESTION.copy()
    question["category_id"] = category_id

    # 테스트용 문제 생성
    response = await test_client.post(
        "/api/v1/qna/questions",
        json={
            "question": question,
            "answers": TEST_ANSWERS
        }
    )

    # 문제 ID 가져오기
    data = response.json()
    question_id = data["question_id"]

    # 문제 업데이트
    updated_data = {
        "question_text": "Python에서 비동기 프로그래밍을 위한 키워드는 무엇인가요?",
        "note": "업데이트된 노트입니다."
    }

    response = await test_client.put(
        f"/api/v1/qna/questions/{question_id}",
        json=updated_data
    )

    # 응답 상태 코드 확인
    assert response.status_code == 200

    # 업데이트 성공 여부 확인
    data = response.json()
    assert data["success"] is True

    # 업데이트된 문제 조회
    response = await test_client.get(f"/api/v1/qna/questions/{question_id}")

    # 업데이트된 필드 확인
    data = response.json()
    assert data["question_text"] == updated_data["question_text"]
    assert data["note"] == updated_data["note"]


@pytest.mark.asyncio
async def test_delete_question(test_client: AsyncClient, test_category: Dict[str, Any]) -> None:
    """문제 삭제 테스트"""
    # 카테고리 ID 설정
    category_id = test_category["category_id"]
    question = TEST_QUESTION.copy()
    question["category_id"] = category_id

    # 테스트용 문제 생성
    response = await test_client.post(
        "/api/v1/qna/questions",
        json={
            "question": question,
            "answers": TEST_ANSWERS
        }
    )

    # 문제 ID 가져오기
    data = response.json()
    question_id = data["question_id"]

    # 문제 삭제
    response = await test_client.delete(f"/api/v1/qna/questions/{question_id}")

    # 응답 상태 코드 확인
    assert response.status_code == 200

    # 삭제 성공 여부 확인
    data = response.json()
    assert data["success"] is True

    # 삭제된 문제 조회 시도 (404 응답 기대)
    response = await test_client.get(f"/api/v1/qna/questions/{question_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_filter_questions_by_category(test_client: AsyncClient, test_category: Dict[str, Any]) -> None:
    """카테고리별 문제 필터링 테스트"""
    # 첫 번째 카테고리 ID 설정
    category_id1 = test_category["category_id"]

    # 두 번째 카테고리 생성
    category2 = {
        "name": "알고리즘",
        "is_use": "Y"
    }
    response = await test_client.post("/api/v1/categories/", json=category2)
    category_id2 = response.json()["category_id"]

    # 첫 번째 카테고리에 문제 생성
    question1 = TEST_QUESTION.copy()
    question1["category_id"] = category_id1
    response = await test_client.post(
        "/api/v1/qna/questions",
        json={
            "question": question1,
            "answers": TEST_ANSWERS
        }
    )

    # 두 번째 카테고리에 문제 생성
    question2 = TEST_QUESTION.copy()
    question2["category_id"] = category_id2
    question2["question_text"] = "알고리즘 복잡도를 나타내는 표기법은?"
    response = await test_client.post(
        "/api/v1/qna/questions",
        json={
            "question": question2,
            "answers": TEST_ANSWERS
        }
    )

    # 첫 번째 카테고리 필터링
    response = await test_client.get(f"/api/v1/qna/questions?category_id={category_id1}")
    assert response.status_code == 200
    data = response.json()
    # 최소 하나 이상의 문제가 있어야 함
    assert len(data) > 0
    # 모든 문제가 첫 번째 카테고리에 속해야 함
    for question in data:
        assert question["category_id"] == category_id1
        assert question["category"]["category_id"] == category_id1

    # 두 번째 카테고리 필터링
    response = await test_client.get(f"/api/v1/qna/questions?category_id={category_id2}")
    assert response.status_code == 200
    data = response.json()
    # 최소 하나 이상의 문제가 있어야 함
    assert len(data) > 0
    # 모든 문제가 두 번째 카테고리에 속해야 함
    for question in data:
        assert question["category_id"] == category_id2
        assert question["category"]["category_id"] == category_id2