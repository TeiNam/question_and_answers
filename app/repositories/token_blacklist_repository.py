# app/repositories/token_blacklist_repository.py
import logging
from datetime import datetime

from asyncmy import Connection

from app.models.token_blacklist import TokenBlacklist, TokenBlacklistCreate
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TokenBlacklistRepository(BaseRepository[TokenBlacklist]):
    """토큰 블랙리스트 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "token_blacklist"
    model_class = TokenBlacklist
    id_column = "id"

    @classmethod
    async def create(cls, token_data: TokenBlacklistCreate, conn: Connection = None) -> int:
        """블랙리스트에 토큰 추가"""
        query = """
        INSERT INTO token_blacklist (user_id, jti, reason, expire_at)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            token_data.user_id,
            token_data.jti,
            token_data.reason,
            token_data.expire_at
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def is_token_blacklisted(cls, jti: str, conn: Connection = None) -> bool:
        """토큰이 블랙리스트에 있는지 확인"""
        query = """
        SELECT COUNT(*) as count FROM token_blacklist
        WHERE jti = %s AND expire_at > %s
        """

        now = datetime.utcnow()
        cursor = await cls.execute_query(query, (jti, now), conn)
        result = await cursor.fetchone()

        count = result["count"] if isinstance(result, dict) else result[0]
        return count > 0

    @classmethod
    async def blacklist_user_tokens(cls, user_id: int, reason: str, conn: Connection = None) -> bool:
        """사용자의 모든 활성 토큰을 블랙리스트에 추가
        (실제로는 토큰을 알 수 없으므로, JWT 디코딩을 통해 활성 토큰 검증에 실패하도록 함)"""
        # 사용자 ID와, jti="user_{user_id}_all"을 사용하는 특수 레코드 생성
        # 이후 토큰 확인 시 사용자 ID로 이 레코드를 확인하여 모든 토큰을 무효화

        # 기존에 같은 패턴의 레코드가 있으면 삭제
        delete_query = """
        DELETE FROM token_blacklist 
        WHERE user_id = %s AND jti = %s
        """

        jti = f"user_{user_id}_all"
        await cls.execute_query(delete_query, (user_id, jti), conn)

        # 새 레코드 생성 (30일 후 만료)
        expire_at = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        expire_at = expire_at.replace(day=expire_at.day + 30)

        query = """
        INSERT INTO token_blacklist (user_id, jti, reason, expire_at)
        VALUES (%s, %s, %s, %s)
        """

        cursor = await cls.execute_query(
            query,
            (user_id, jti, reason, expire_at),
            conn
        )

        return cursor.rowcount > 0

    @classmethod
    async def clean_expired_tokens(cls, conn: Connection = None) -> int:
        """만료된 토큰 레코드 정리"""
        query = """
        DELETE FROM token_blacklist
        WHERE expire_at < %s
        """

        now = datetime.utcnow()
        cursor = await cls.execute_query(query, (now,), conn)

        return cursor.rowcount
