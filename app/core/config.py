# app/core/config.py
import os
from typing import List

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Settings:
    # 기본 환경 설정
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    VERSION: str = "0.1.0"
    PROJECT_NAME: str = "QnA API"
    PROJECT_DESCRIPTION: str = "비동기 방식의 문답 시스템 API"
    API_V1_STR: str = "/api/v1"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS 설정
    # 단순히 문자열을 분할하는 방식으로 처리
    _origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _origins.split(",") if origin.strip()]

    # MySQL 설정
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "qna")

    # JWT 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-please-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"  # 알 수 없는 필드는 무시


# 설정 인스턴스 생성
settings = Settings()