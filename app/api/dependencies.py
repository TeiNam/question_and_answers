# app/api/dependencies.py
from typing import Tuple, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
import jwt
from app.core.config import settings
from app.models.user import User
from app.services.user_service import UserService
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.repositories.token_blacklist_repository import TokenBlacklistRepository

# OAuth2 로그인 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_token_data(token: str = Depends(oauth2_scheme)) -> Dict:
    """토큰에서 데이터 추출 (블랙리스트 확인 포함)"""
    try:
        # 토큰 디코딩
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # 기본 필드 확인
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        jti: str = payload.get("jti")

        if email is None or user_id is None:
            raise UnauthorizedException("유효하지 않은 인증 정보")

        # JWT ID 확인
        if jti is None:
            raise UnauthorizedException("유효하지 않은 토큰 형식")

        # 토큰 블랙리스트 확인
        is_blacklisted = await TokenBlacklistRepository.is_token_blacklisted(jti)

        # 사용자의 모든 토큰 무효화 확인
        special_jti = f"user_{user_id}_all"
        is_user_blacklisted = await TokenBlacklistRepository.is_token_blacklisted(special_jti)

        if is_blacklisted or is_user_blacklisted:
            raise UnauthorizedException("만료된 토큰입니다. 다시 로그인해주세요.")

        # 추가 권한 정보
        is_admin: bool = payload.get("is_admin", False)
        role: str = payload.get("role", "solver")  # 기본값은 일반 사용자

        return {
            "email": email,
            "user_id": user_id,
            "jti": jti,
            "is_admin": is_admin,
            "role": role
        }
    except PyJWTError:
        raise UnauthorizedException("인증 정보가 만료되었거나 유효하지 않습니다")
    except UnauthorizedException:
        raise


async def get_current_user(token_data: Dict = Depends(get_token_data)) -> User:
    """현재 인증된 사용자 가져오기"""
    user_id = token_data.get("user_id")

    # 사용자 정보 조회
    user = await UserService.get_user_by_id(user_id)

    # 계정이 활성 상태인지 확인
    if user.is_active != "Y":
        raise UnauthorizedException("계정이 비활성화되었습니다")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """현재 활성 상태인 사용자 가져오기 (추가 검증 시 확장 가능)"""
    if current_user.is_active != "Y":
        raise UnauthorizedException("계정이 비활성화되었습니다")
    return current_user


async def get_current_admin_user(
        token_data: Dict = Depends(get_token_data),
        current_user: User = Depends(get_current_user)
) -> User:
    """현재 관리자 권한을 가진 사용자 가져오기 (JWT 토큰에서 확인)"""
    if not token_data.get("is_admin", False):
        raise ForbiddenException("관리자 권한이 필요합니다")
    return current_user


async def get_user_by_role(
        role: str,
        token_data: Dict = Depends(get_token_data),
        current_user: User = Depends(get_current_user)
) -> User:
    """특정 역할을 가진 사용자 가져오기 (JWT 토큰에서 확인)"""
    if token_data.get("role") != role:
        raise ForbiddenException(f"{role} 역할이 필요합니다")
    return current_user