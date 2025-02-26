# app/api/routes/__init__.py
from fastapi import APIRouter
from app.api.routes import qna, category

api_router = APIRouter()

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