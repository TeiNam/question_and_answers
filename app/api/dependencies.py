# app/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
import jwt
from app.core.config import settings
from app.models.user import User
from app.services.user_service import UserService
from app.core.exceptions import UnauthorizedException

# OAuth2 로그인 스키마 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """현재 인증된 사용자 가져오기"""
    try:
        # 토큰 디코딩
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # 토큰에서 이메일과 사용자 ID 추출
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None or user_id is None:
            raise UnauthorizedException("유효하지 않은 인증 정보")

    except PyJWTError:
        raise UnauthorizedException("인증 정보가 만료되었거나 유효하지 않습니다")

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


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """현재 관리자 권한을 가진 사용자 가져오기"""
    if current_user.is_admin != "Y":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user