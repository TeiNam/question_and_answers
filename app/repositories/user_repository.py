# app/repositories/user_repository.py
import logging
from typing import Optional, List
from asyncmy import Connection
from app.models.user import User, UserCreate, UserUpdate
from app.repositories.base_repository import BaseRepository
from app.core.auth import get_password_hash

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """사용자 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "user"
    model_class = User
    id_column = "user_id"

    @classmethod
    async def create(cls, user: UserCreate, conn: Connection = None) -> int:
        """새 사용자 생성 (비밀번호 해싱 처리)"""
        # 비밀번호 해싱
        hashed_password = get_password_hash(user.password)

        query = """
        INSERT INTO user (email, username, password, is_active, is_admin, role)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            user.email,
            user.username,
            hashed_password,
            user.is_active,
            user.is_admin,
            user.role
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_by_email(cls, email: str, conn: Connection = None) -> Optional[User]:
        """이메일로 사용자 조회"""
        query = "SELECT * FROM user WHERE email = %s"

        cursor = await cls.execute_query(query, (email,), conn)
        result = await cursor.fetchone()

        return User(**result) if result else None

    @classmethod
    async def update_password(cls, user_id: int, hashed_password: str, conn: Connection = None) -> bool:
        """사용자 비밀번호 업데이트"""
        query = "UPDATE user SET password = %s WHERE user_id = %s"

        cursor = await cls.execute_query(query, (hashed_password, user_id), conn)
        return cursor.rowcount > 0

    @classmethod
    async def update(cls, user_id: int, user_update: UserUpdate, conn: Connection = None) -> bool:
        """사용자 정보 업데이트 (비밀번호가 있는 경우 해싱 처리)"""
        # 업데이트할 데이터 준비
        update_dict = user_update.dict(exclude_unset=True)

        # 비밀번호가 있는 경우 해싱 처리
        if 'password' in update_dict:
            update_dict['password'] = get_password_hash(update_dict['password'])

        # 기본 업데이트 메서드 사용
        return await super().update(user_id, update_dict, conn)

    @classmethod
    async def get_users_by_role(cls, role: str, conn: Connection = None) -> List[User]:
        """역할별 사용자 목록 조회"""
        query = "SELECT * FROM user WHERE role = %s ORDER BY user_id"

        cursor = await cls.execute_query(query, (role,), conn)
        results = await cursor.fetchall()

        return [User(**result) for result in results]