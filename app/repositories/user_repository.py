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

        # 결과가 없으면 None 반환
        if not result:
            return None

        # 튜플 결과를 딕셔너리로 변환
        if not isinstance(result, dict) and hasattr(cursor, 'description'):
            column_names = [column[0] for column in cursor.description]
            result_dict = dict(zip(column_names, result))
            return User(**result_dict)
        else:
            # 이미 딕셔너리 형태인 경우
            return User(**result)

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
        rows = await cursor.fetchall()

        # 결과가 없으면 빈 리스트 반환
        if not rows:
            return []

        # 튜플 결과를 딕셔너리로 변환 (첫 번째 결과가 딕셔너리가 아닌 경우)
        if rows and not isinstance(rows[0], dict) and hasattr(cursor, 'description'):
            column_names = [column[0] for column in cursor.description]
            result_dicts = [dict(zip(column_names, row)) for row in rows]
            return [User(**result_dict) for result_dict in result_dicts]
        else:
            # 이미 딕셔너리 형태인 경우
            return [User(**row) for row in rows]