# app/services/user_service.py
import logging
from typing import Dict, Any, Optional
from datetime import timedelta
from app.models.user import User, UserCreate, UserLogin, UserUpdate
from app.repositories.user_repository import UserRepository
from app.core.exceptions import NotFoundException, ValidationException, UnauthorizedException, DatabaseException
from app.core.auth import verify_password, get_password_hash, create_access_token, create_user_response
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    async def register(user_data: UserCreate) -> Dict[str, Any]:
        """새 사용자 등록"""
        try:
            # 이메일 중복 체크
            existing_user = await UserRepository.get_by_email(user_data.email)
            if existing_user:
                raise ValidationException(f"이메일 '{user_data.email}'은 이미 사용 중입니다.")

            # 사용자 생성
            user_id = await UserRepository.create(user_data)

            # 생성된 사용자 정보 조회
            user = await UserRepository.get_by_id(user_id)

            # 액세스 토큰 생성
            access_token = create_access_token(
                data={"sub": user.email, "user_id": user.user_id}
            )

            # 로그 기록
            logger.info(f"새 사용자 등록: {user.email} (ID: {user.user_id})")

            # 응답 데이터 생성
            return create_user_response(user, access_token)

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"사용자 등록 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def login(login_data: UserLogin) -> Dict[str, Any]:
        """사용자 로그인"""
        try:
            # 이메일로 사용자 조회
            user = await UserRepository.get_by_email(login_data.email)
            if not user:
                raise UnauthorizedException("이메일 또는 비밀번호가 잘못되었습니다.")

            # 비밀번호 검증
            if not verify_password(login_data.password, user.password):
                raise UnauthorizedException("이메일 또는 비밀번호가 잘못되었습니다.")

            # 계정이 활성 상태인지 확인
            if user.is_active != "Y":
                raise UnauthorizedException("계정이 비활성화되었습니다.")

            # 액세스 토큰 생성
            access_token = create_access_token(
                data={"sub": user.email, "user_id": user.user_id}
            )

            # 로그 기록
            logger.info(f"로그인 성공: {user.email} (ID: {user.user_id})")

            # 응답 데이터 생성
            return create_user_response(user, access_token)

        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"로그인 중 오류 발생: {e}")
            raise DatabaseException(str(e))

    @staticmethod
    async def get_user_by_id(user_id: int) -> User:
        """ID로 사용자 조회"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"ID가 {user_id}인 사용자를 찾을 수 없습니다.")
        return user

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return await UserRepository.get_by_email(email)

    @staticmethod
    async def update_user(user_id: int, user_update: UserUpdate) -> Dict[str, Any]:
        """사용자 정보 업데이트"""
        try:
            # 사용자 존재 확인
            user = await UserRepository.get_by_id(user_id)
            if not user:
                raise NotFoundException(f"ID가 {user_id}인 사용자를 찾을 수 없습니다.")

            # 이메일 업데이트 시 중복 체크
            if user_update.email and user_update.email != user.email:
                existing_user = await UserRepository.get_by_email(user_update.email)
                if existing_user:
                    raise ValidationException(f"이메일 '{user_update.email}'은 이미 사용 중입니다.")

            # 사용자 정보 업데이트
            success = await UserRepository.update(user_id, user_update)

            # 업데이트된 사용자 정보 조회
            updated_user = await UserRepository.get_by_id(user_id)

            # 로그 기록
            update_fields = ', '.join(k for k, v in user_update.dict(exclude_unset=True).items() if v is not None)
            logger.info(f"사용자 정보 업데이트 (ID: {user_id}) - 필드: {update_fields}")

            return {
                "success": success,
                "message": "사용자 정보가 성공적으로 업데이트되었습니다.",
                "user": {
                    "user_id": updated_user.user_id,
                    "email": updated_user.email,
                    "username": updated_user.username,
                    "is_admin": updated_user.is_admin == "Y",
                    "is_active": updated_user.is_active == "Y"
                }
            }

        except NotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"사용자 정보 업데이트 중 오류 발생: {e}")
            raise DatabaseException(str(e))