# app/core/auth.py
import jwt
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
from app.core.config import settings
from typing import Optional, Dict, Any
from app.models.user import User

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """일반 텍스트 비밀번호와 해시된 비밀번호를 비교"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호를 해시화"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성 (JTI 포함)"""
    to_encode = data.copy()

    # 만료 시간 설정
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # 고유 JWT ID 생성
    jti = str(uuid.uuid4())

    # 토큰 데이터에 만료 시간과 JTI 추가
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "iat": datetime.utcnow()  # 발행 시간
    })

    # JWT 인코딩
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_user_response(user: User, access_token: str) -> Dict[str, Any]:
    """사용자 응답 데이터 생성"""
    # 토큰에서 데이터 추출하여 응답에 포함
    try:
        token_data = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # 토큰에서 is_admin과 role 값을 추출
        is_admin = token_data.get("is_admin", False)
        role = token_data.get("role", "solver")

    except:
        # 토큰 디코딩에 실패하면 기본값 사용
        is_admin = user.is_admin == "Y"
        role = user.role

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "is_admin": is_admin,
            "role": role
        }
    }