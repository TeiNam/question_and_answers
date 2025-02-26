# tests/test_qna_api.py
import asyncio

import pytest
from httpx import AsyncClient

from main import app

# 테스트용 관리자 계정
TEST_ADMIN = {
    "email": "admin@test.com",
    "username": "관리자",
    "password": "securepassword123",
    "is_admin": "Y"
}

# 테스트용 일반 사용자 계정
TEST_USER = {
    "email": "user@test.com",
    "username": "사용자",
    "password": "userpassword123"
}

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
    {"answer_text": "async/await", "is_correct": "Y", "note": "정답입니다."},
    {"answer_text": "yield/return", "is_correct": "N", "note": "Generator에 사용되는 키워드입니다."},
    {"answer_text": "try/except", "is_correct": "N", "note": "예외 처리에 사용되는 키워드입니다."},
    {"answer_text": "if/else", "is_correct": "N", "note": "조건문에 사용되는 키워드입니다."}
]


@pytest.fixture(scope="module")
def event_loop():
    """pytest에서 asyncio 이벤트 루프 생성"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    """비동기 테스트 클라이언트 설정"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def admin_token(async_client):
    """관리자 토큰 발급"""
    # 먼저 관리자 계정 등록
    response = await async_client.post("/api/v1/auth/register", json=TEST_ADMIN)
    if response.status_code == 400:  # 이미 등록된 경우 로그인 시도
        response = await async_client.post("/api/v1/auth/login", json={
            "email": TEST_ADMIN["email"],
            "password": TEST_ADMIN["password"]
        })

    assert response.status_code in [200, 201]
    return response.json()["access_token"]


@pytest.fixture
async def user_token(async_client):
    """일반 사용자 토큰 발급"""
    # 일반 사용자 계정 등록
    response = await async_client.post("/api/v1/auth/register", json=TEST_USER)
    if response.status_code == 400:  # 이미 등록된 경우 로그인 시도
        response = await async_client.post("/api/v1/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        })

    assert response.status_code in [200, 201]
    return response.json()["access_token"]


@pytest.fixture
async def test_category(async_client, admin_token):
    """테스트용La 카테고리 생성"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.post(
        "/api/v1/categories/",
        json=TEST_CATEGORY,
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert "category_id" in data

    yield data

    # 테스트 후 카테고리 정리 (선택적)
    # await async_client.delete(f"/api/v1/categories/{data['category_id']}", headers=headers)


@pytest.mark.asyncio
async def test_category_crud(async_client, admin_token):
    """카테고리 CRUD 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. 카테고리 생성
    test_category_data = {
        "name": "테스트 카테고리",
        "is_use": "Y"
    }
    response = await async_client.post(
        "/api/v1/categories/",
        json=test_category_data,
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "category_id" in data

    category_id = data["category_id"]

    # 2. 카테고리 조회
    response = await async_client.get(
        f"/api/v1/categories/{category_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["category_id"] == category_id
    assert data["name"] == test_category_data["name"]

    # 3. 카테고리 목록 조회
    response = await async_client.get(
        "/api/v1/categories/",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(category["category_id"] == category_id for category in data)

    # 4. 카테고리 업데이트
    update_data = {
        "name": "업데이트된 카테고리명",
        "is_use": "Y"
    }

    response = await async_client.put(
        f"/api/v1/categories/{category_id}",
        json=update_data,
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # 업데이트 확인
    response = await async_client.get(
        f"/api/v1/categories/{category_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]

    # 5. 카테고리 필터링 테스트
    response = await async_client.get(
        "/api/v1/categories/?is_use=Y",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    for category in data:
        assert category["is_use"] == "Y"


@pytest.mark.asyncio
async def test_create_question_with_answers(async_client, admin_token, test_category):
    """문제 및 답변 생성 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 카테고리 ID 설정
    category_id = test_category["category_id"]
    question = TEST_QUESTION.copy()
    question["category_id"] = category_id

    # 문제와 답변 생성
    response = await async_client.post(
        "/api/v1/qna/questions",
        json={
            "question": question,
            "answers": TEST_ANSWERS
        },
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "question_id" in data
    assert "answer_ids" in data
    assert len(data["answer_ids"]) == len(TEST_ANSWERS)

    return data["question_id"], data["answer_ids"]


@pytest.mark.asyncio
async def test_get_question_with_answers(async_client, admin_token, test_category):
    """문제 및 답변 조회 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 먼저 문제 생성
    question_id, _ = await test_create_question_with_answers(async_client, admin_token, test_category)

    # 생성된 문제 조회
    response = await async_client.get(
        f"/api/v1/qna/questions/{question_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question_id"] == question_id
    assert data["category_id"] == test_category["category_id"]
    assert data["question_text"] == TEST_QUESTION["question_text"]
    assert len(data["answers"]) == len(TEST_ANSWERS)

    # 카테고리 정보 확인
    assert "category" in data
    assert data["category"]["category_id"] == test_category["category_id"]

    # 답변 정보 확인
    for i, answer in enumerate(data["answers"]):
        assert answer["answer_text"] == TEST_ANSWERS[i]["answer_text"]
        assert answer["is_correct"] == TEST_ANSWERS[i]["is_correct"]


@pytest.mark.asyncio
async def test_get_all_questions(async_client, admin_token, test_category):
    """모든 문제 조회 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 여러 문제 생성
    for i in range(3):
        question = TEST_QUESTION.copy()
        question["category_id"] = test_category["category_id"]
        question["question_text"] = f"테스트 문제 {i + 1}"

        await async_client.post(
            "/api/v1/qna/questions",
            json={
                "question": question,
                "answers": TEST_ANSWERS
            },
            headers=headers
        )

    # 전체 문제 목록 조회
    response = await async_client.get(
        "/api/v1/qna/questions",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # 페이지네이션 테스트
    response = await async_client.get(
        "/api/v1/qna/questions?skip=0&limit=2",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


@pytest.mark.asyncio
async def test_update_question(async_client, admin_token, test_category):
    """문제 업데이트 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 먼저 문제 생성
    question_id, _ = await test_create_question_with_answers(async_client, admin_token, test_category)

    # 문제 업데이트
    update_data = {
        "question_text": "업데이트된 문제 내용",
        "note": "업데이트된 노트입니다."
    }

    response = await async_client.put(
        f"/api/v1/qna/questions/{question_id}",
        json=update_data,
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # 업데이트 확인
    response = await async_client.get(
        f"/api/v1/qna/questions/{question_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["question_text"] == update_data["question_text"]
    assert data["note"] == update_data["note"]


@pytest.mark.asyncio
async def test_update_answer(async_client, admin_token, test_category):
    """답변 업데이트 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 먼저 문제와 답변 생성
    _, answer_ids = await test_create_question_with_answers(async_client, admin_token, test_category)

    # 첫 번째 답변 업데이트
    answer_id = answer_ids[0]
    update_data = {
        "answer_text": "업데이트된 답변 내용",
        "note": "업데이트된 노트"
    }

    response = await async_client.put(
        f"/api/v1/qna/answers/{answer_id}",
        json=update_data,
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_submit_answer(async_client, user_token, admin_token, test_category):
    """답변 제출 테스트"""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 먼저 문제와 답변 생성 (관리자 권한)
    question_id, answer_ids = await test_create_question_with_answers(async_client, admin_token, test_category)

    # 정답 제출 (일반 사용자)
    response = await async_client.post(
        "/api/v1/qna/submit",
        json={
            "question_id": question_id,
            "selected_answer_ids": [answer_ids[0]]  # 첫 번째 답변이 정답
        },
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_correct"] is True
    assert len(data["incorrect_selections"]) == 0

    # 오답 제출 (일반 사용자)
    response = await async_client.post(
        "/api/v1/qna/submit",
        json={
            "question_id": question_id,
            "selected_answer_ids": [answer_ids[1]]  # 두 번째 답변은 오답
        },
        headers=user_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["is_correct"] is False
    assert len(data["incorrect_selections"]) == 1


@pytest.mark.asyncio
async def test_delete_question(async_client, admin_token, test_category):
    """문제 삭제 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 먼저 문제 생성
    question_id, _ = await test_create_question_with_answers(async_client, admin_token, test_category)

    # 문제 삭제
    response = await async_client.delete(
        f"/api/v1/qna/questions/{question_id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # 삭제 확인
    response = await async_client.get(
        f"/api/v1/qna/questions/{question_id}",
        headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_filter_questions_by_category(async_client, admin_token):
    """카테고리별 문제 필터링 테스트"""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 첫 번째 카테고리 생성
    response = await async_client.post(
        "/api/v1/categories/",
        json={"name": "카테고리1", "is_use": "Y"},
        headers=headers
    )
    category_id1 = response.json()["category_id"]

    # 두 번째 카테고리 생성
    response = await async_client.post(
        "/api/v1/categories/",
        json={"name": "카테고리2", "is_use": "Y"},
        headers=headers
    )
    category_id2 = response.json()["category_id"]

    # 첫 번째 카테고리에 문제 생성
    question1 = TEST_QUESTION.copy()
    question1["category_id"] = category_id1
    question1["question_text"] = "카테고리1 문제"

    await async_client.post(
        "/api/v1/qna/questions",
        json={"question": question1, "answers": TEST_ANSWERS},
        headers=headers
    )

    # 두 번째 카테고리에 문제 생성
    question2 = TEST_QUESTION.copy()
    question2["category_id"] = category_id2
    question2["question_text"] = "카테고리2 문제"

    await async_client.post(
        "/api/v1/qna/questions",
        json={"question": question2, "answers": TEST_ANSWERS},
        headers=headers
    )

    # 첫 번째 카테고리로 필터링
    response = await async_client.get(
        f"/api/v1/qna/questions?category_id={category_id1}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for q in data:
        assert q["category_id"] == category_id1

    # 두 번째 카테고리로 필터링
    response = await async_client.get(
        f"/api/v1/qna/questions?category_id={category_id2}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for q in data:
        assert q["category_id"] == category_id2


@pytest.mark.asyncio
async def test_user_score_tracking(async_client, user_token, admin_token, test_category):
    """사용자 성적 추적 테스트"""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 먼저 문제와 답변 생성 (관리자 권한)
    question_id, answer_ids = await test_create_question_with_answers(async_client, admin_token, test_category)

    # 사용자가 답변 제출
    await async_client.post(
        "/api/v1/qna/submit",
        json={
            "question_id": question_id,
            "selected_answer_ids": [answer_ids[0]]  # 정답 제출
        },
        headers=user_headers
    )

    # 사용자 성적 이력 조회
    response = await async_client.get(
        "/api/v1/scores/history",
        headers=user_headers
    )

    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    assert len(history) > 0

    # 사용자 성적 요약 조회
    response = await async_client.get(
        "/api/v1/scores/summary",
        headers=user_headers
    )

    assert response.status_code == 200
    summary = response.json()
    assert summary["total_questions"] > 0
    assert "accuracy_rate" in summary

    # 정확도가 0에서 100 사이인지 확인
    assert 0 <= summary["accuracy_rate"] <= 100