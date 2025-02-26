# app/repositories/group_repository.py
import logging
from typing import List, Dict, Any

from asyncmy import Connection

from app.models.group import Group, GroupCreate, GroupMember, GroupMemberCreate
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class GroupRepository(BaseRepository[Group]):
    """그룹 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "user_group"
    model_class = Group
    id_column = "group_id"

    @classmethod
    async def create_group(cls, group: GroupCreate, conn: Connection = None) -> int:
        """새 그룹 생성"""
        query = """
        INSERT INTO user_group (name, description, user_id)
        VALUES (%s, %s, %s)
        """
        values = (
            group.name,
            group.description,
            group.user_id
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_groups_by_creator(cls, user_id: int, conn: Connection = None) -> List[Group]:
        """출제자 ID로 그룹 목록 조회"""
        where_clause = "user_id = %s"
        params = (user_id,)

        return await super().get_all(
            where_clause=where_clause,
            params=params,
            order_by="name ASC",
            conn=conn
        )

    @classmethod
    async def get_groups_by_member(cls, user_id: int, conn: Connection = None) -> List[Group]:
        """사용자가 속한 그룹 목록 조회"""
        query = """
        SELECT g.* 
        FROM user_group g
        JOIN group_member gm ON g.group_id = gm.group_id
        WHERE gm.user_id = %s
        ORDER BY g.name ASC
        """

        cursor = await cls.execute_query(query, (user_id,), conn)
        results = await cursor.fetchall()

        return [Group(**result) for result in results]

    @classmethod
    async def get_group_with_members(cls, group_id: int, conn: Connection = None) -> Dict[str, Any]:
        """그룹 및 멤버 목록 조회"""
        # 그룹 정보 조회
        group = await cls.get_by_id(group_id, conn)
        if not group:
            return None

        # 멤버 목록 조회
        query = """
        SELECT user_id FROM group_member WHERE group_id = %s
        """
        cursor = await cls.execute_query(query, (group_id,), conn)
        members = await cursor.fetchall()

        member_ids = [member["user_id"] for member in members]

        return {
            **group.dict(),
            "members": member_ids
        }


class GroupMemberRepository(BaseRepository[GroupMember]):
    """그룹 멤버 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "group_member"
    model_class = GroupMember
    id_column = "member_id"

    @classmethod
    async def add_member(cls, member: GroupMemberCreate, conn: Connection = None) -> int:
        """그룹에 멤버 추가"""
        query = """
        INSERT INTO group_member (group_id, user_id)
        VALUES (%s, %s)
        """
        values = (
            member.group_id,
            member.user_id
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def remove_member(cls, group_id: int, user_id: int, conn: Connection = None) -> bool:
        """그룹에서 멤버 제거"""
        query = """
        DELETE FROM group_member WHERE group_id = %s AND user_id = %s
        """
        cursor = await cls.execute_query(query, (group_id, user_id), conn)
        return cursor.rowcount > 0

    @classmethod
    async def is_member(cls, group_id: int, user_id: int, conn: Connection = None) -> bool:
        """사용자가 그룹 멤버인지 확인"""
        query = """
        SELECT COUNT(*) as count FROM group_member 
        WHERE group_id = %s AND user_id = %s
        """
        cursor = await cls.execute_query(query, (group_id, user_id), conn)
        result = await cursor.fetchone()
        return result["count"] > 0

    @classmethod
    async def get_members(cls, group_id: int, conn: Connection = None) -> List[int]:
        """그룹 멤버 목록 조회"""
        query = """
        SELECT user_id FROM group_member WHERE group_id = %s
        """
        cursor = await cls.execute_query(query, (group_id,), conn)
        results = await cursor.fetchall()
        return [result["user_id"] for result in results]