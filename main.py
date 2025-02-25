# main.py
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import importlib
import os
import glob
from app.core.config import settings
from app.core.database import close_db_connections
from app.api.routes import api_router
from contextlib import asynccontextmanager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 시작 및 종료 이벤트 처리를 위한 컨텍스트 매니저
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    logger.info("서버 시작 중... 🚀")
    yield
    # 종료 시 실행
    logger.info("서버 종료 중... 👋")
    await close_db_connections()

# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 추가
app.include_router(api_router, prefix=settings.API_V1_STR)

# 상태 확인 엔드포인트
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "서버 정상 작동 중... 건강해요! 💪"}

if __name__ == "__main__":
    import uvicorn
    # 서버 실행 (개발 환경용)
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )