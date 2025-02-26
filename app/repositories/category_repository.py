# app/repositories/category_repository.py
import logging
from typing import List, Optional

from asyncmy import Connection

from app.models.category import Category, CategoryCreate
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CategoryRepository(BaseRepository[Category]):
    """카테고리 관련 데이터베이스 작업을 처리하는 레포지토리"""

    table_name = "category"
    model_class = Category
    id_column = "category_id"

    @classmethod
    async def create(cls, category: CategoryCreate, conn: Connection = None) -> int:
        """새 카테고리 생성"""
        query = """
        INSERT INTO category (name, is_use)
        VALUES (%s, %s)
        """
        values = (
            category.name,
            category.is_use
        )

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_all(cls,
                      is_use: Optional[str] = None,
                      conn: Connection = None) -> List[Category]:
        """모든 카테고리 조회 (사용 상태 필터링 옵션)"""
        where_clause = "is_use = %s" if is_use else ""
        params = (is_use,) if is_use else None

        return await super().get_all(
            where_clause=where_clause,
            params=params,
            order_by="name ASC",
            conn=conn
        )