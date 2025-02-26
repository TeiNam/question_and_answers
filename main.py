# main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import close_db_connections, init_db_pool
from app.core.exceptions import NotFoundException, DatabaseException, ValidationException

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
    await init_db_pool()
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

# 전역 예외 핸들러
@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail},
    )

@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    return JSONResponse(
        status_code=500,
        content={"detail": exc.detail},
    )

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.detail},
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