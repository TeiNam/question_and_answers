# app/api/routes/__init__.py
from fastapi import APIRouter
from app.api.routes import qna, category, auth, user_score, quiz

api_router = APIRouter()

# 인증 관련 엔드포인트
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# 카테고리 관련 엔드포인트
api_router.include_router(
    category.router,
    prefix="/categories",
    tags=["Categories"]
)

# QnA 관련 엔드포인트
api_router.include_router(
    qna.router,
    prefix="/qna",
    tags=["QnA"]
)

# 퀴즈 관련 엔드포인트
api_router.include_router(
    quiz.router,
    prefix="/quiz",
    tags=["Quiz"]
)

# 사용자 성적 관련 엔드포인트
api_router.include_router(
    user_score.router,
    prefix="/scores",
    tags=["User Scores"]
)