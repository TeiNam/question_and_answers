# app/repositories/role_request_repository.py
import logging
from datetime import datetime
from typing import List, Optional

from asyncmy import Connection

from app.models.role_request import RoleRequest, RoleRequestCreate
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RoleRequestRepository(BaseRepository[RoleRequest]):
    """역할 변경 요청 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "role_request"
    model_class = RoleRequest
    id_column = "request_id"

    @classmethod
    async def create(cls, role_request: RoleRequestCreate, conn: Connection = None) -> int:
        """새 역할 변경 요청 생성"""
        query = """
        INSERT INTO role_request (user_id, requested_role, reason, status)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            role_request.user_id,
            role_request.requested_role,
            role_request.reason,
            role_request.status
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_pending_requests(cls, conn: Connection = None) -> List[RoleRequest]:
        """대기 중인 모든 요청 조회"""
        return await cls.get_all(
            where_clause="status = %s",
            params=("pending",),
            order_by="create_at ASC",  # 변경: created_at → create_at
            conn=conn
        )

    @classmethod
    async def get_user_requests(cls, user_id: int, conn: Connection = None) -> List[RoleRequest]:
        """특정 사용자의 모든 요청 조회"""
        return await cls.get_all(
            where_clause="user_id = %s",
            params=(user_id,),
            order_by="create_at DESC",  # 변경: created_at → create_at
            conn=conn
        )

    @classmethod
    async def get_latest_pending_request(cls, user_id: int, conn: Connection = None) -> Optional[RoleRequest]:
        """사용자의 가장 최근 대기 중인 요청 조회"""
        query = """
        SELECT * FROM role_request
        WHERE user_id = %s AND status = 'pending'
        ORDER BY create_at DESC  
        LIMIT 1
        """

        cursor = await cls.execute_query(query, (user_id,), conn)
        result = await cursor.fetchone()

        if not result:
            return None

        if not isinstance(result, dict) and hasattr(cursor, 'description'):
            column_names = [column[0] for column in cursor.description]
            result_dict = dict(zip(column_names, result))
            return cls.model_class(**result_dict)
        else:
            return cls.model_class(**result)

    @classmethod
    async def update_status(cls,
                            request_id: int,
                            status: str,
                            admin_id: int,
                            admin_comment: Optional[str] = None,
                            conn: Connection = None) -> bool:
        """요청 상태 업데이트"""
        query = """
        UPDATE role_request 
        SET status = %s, processed_by = %s, process_at = %s, admin_comment = %s
        WHERE request_id = %s
        """

        process_at = datetime.utcnow()  # 변경: processed_at → process_at

        cursor = await cls.execute_query(
            query,
            (status, admin_id, process_at, admin_comment, request_id),
            conn
        )
        return cursor.rowcount > 0
