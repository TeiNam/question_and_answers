# app/repositories/category_repository.py
import logging
from typing import List, Optional
from app.models.category import Category, CategoryCreate, CategoryUpdate
from app.core.database import get_mysql_connection

logger = logging.getLogger(__name__)


class CategoryRepository:
    @staticmethod
    async def create(category: CategoryCreate, conn=None) -> int:
        """새 카테고리 생성"""
        query = """
        INSERT INTO category (name, is_use)
        VALUES (%s, %s)
        """
        values = (
            category.name,
            category.is_use
        )

        if conn:
            # 외부에서 커넥션이 제공된 경우
            async with conn.cursor() as cursor:
                await cursor.execute(query, values)
                return cursor.lastrowid
        else:
            # 커넥션 생성
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, values)
                    return cursor.lastrowid

    @staticmethod
    async def get_by_id(category_id: int, conn=None) -> Optional[Category]:
        """ID로 카테고리 조회"""
        query = "SELECT * FROM category WHERE category_id = %s"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (category_id,))
                result = await cursor.fetchone()
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (category_id,))
                    result = await cursor.fetchone()

        return Category(**result) if result else None

    @staticmethod
    async def get_all(is_use: Optional[str] = None, conn=None) -> List[Category]:
        """모든 카테고리 조회 (사용 상태 필터링 옵션)"""
        query = "SELECT * FROM category"
        params = []

        # 사용 여부 필터링
        if is_use:
            query += " WHERE is_use = %s"
            params.append(is_use)

        # 정렬
        query += " ORDER BY name ASC"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                results = await cursor.fetchall()
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    results = await cursor.fetchall()

        return [Category(**result) for result in results]

    @staticmethod
    async def update(
            category_id: int,
            category_update: CategoryUpdate,
            conn=None
    ) -> bool:
        """카테고리 업데이트"""
        # 업데이트할 필드 구성 (None이 아닌 필드만)
        update_fields = {}
        if category_update.name is not None:
            update_fields["name"] = category_update.name
        if category_update.is_use is not None:
            update_fields["is_use"] = category_update.is_use

        if not update_fields:
            return True  # 업데이트할 필드가 없음

        # 쿼리 구성
        set_clause = ", ".join(f"{field} = %s" for field in update_fields.keys())
        query = f"UPDATE category SET {set_clause} WHERE category_id = %s"

        # 파라미터 구성
        params = list(update_fields.values())
        params.append(category_id)

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.rowcount > 0
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    return cursor.rowcount > 0

    @staticmethod
    async def delete(category_id: int, conn=None) -> bool:
        """카테고리 삭제"""
        query = "DELETE FROM category WHERE category_id = %s"

        if conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (category_id,))
                return cursor.rowcount > 0
        else:
            pool = await get_mysql_connection()
            async with pool as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, (category_id,))
                    return cursor.rowcount > 0