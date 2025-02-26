# app/repositories/base_repository.py
import logging
from typing import Dict, List, Optional, TypeVar, Generic, Type, Union

from asyncmy import Connection
from pydantic import BaseModel

from app.core.database import get_db

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """기본 레포지토리 클래스"""

    table_name: str
    model_class: Type[T]
    id_column: str

    @classmethod
    async def execute_query(cls, query: str, params: tuple = None, conn: Connection = None, auto_close: bool = True):
        """쿼리 실행 및 커넥션 관리 공통 메서드"""
        if conn:
            async with conn.cursor() as cursor:  # dictionary=True 제거
                await cursor.execute(query, params)
                return cursor
        else:
            db_gen = get_db()
            conn = await db_gen.__anext__()
            try:
                async with conn.cursor() as cursor:  # dictionary=True 제거
                    await cursor.execute(query, params)
                    return cursor
            finally:
                if auto_close:
                    try:
                        await db_gen.__anext__()
                    except StopAsyncIteration:
                        pass

    @classmethod
    async def create(cls, item: BaseModel, conn: Connection = None) -> int:
        """새 레코드 생성"""
        # 모델에서 dictionary로 변환
        item_dict = item.dict(exclude_unset=True)

        # SQL 쿼리 및 파라미터 구성
        fields = ', '.join(item_dict.keys())
        placeholders = ', '.join(['%s'] * len(item_dict))
        values = tuple(item_dict.values())

        query = f"INSERT INTO {cls.table_name} ({fields}) VALUES ({placeholders})"

        cursor = await cls.execute_query(query, values, conn)
        return cursor.lastrowid

    @classmethod
    async def get_by_id(cls, id_value: int, conn: Connection = None) -> Optional[T]:
        """ID로 레코드 조회"""
        query = f"SELECT * FROM {cls.table_name} WHERE {cls.id_column} = %s"

        cursor = await cls.execute_query(query, (id_value,), conn)
        result = await cursor.fetchone()

        # 결과가 없으면 None 반환
        if not result:
            return None

        # 튜플 결과를 딕셔너리로 변환
        if not isinstance(result, dict) and hasattr(cursor, 'description'):
            column_names = [column[0] for column in cursor.description]
            result_dict = dict(zip(column_names, result))
            return cls.model_class(**result_dict)
        else:
            # 이미 딕셔너리 형태인 경우
            return cls.model_class(**result)

    @classmethod
    async def get_all(cls,
                      where_clause: str = "",
                      params: tuple = None,
                      order_by: str = None,
                      limit: int = None,
                      offset: int = None,
                      conn: Connection = None) -> List[T]:
        """조건에 맞는 모든 레코드 조회"""
        query = f"SELECT * FROM {cls.table_name}"

        # WHERE 절 추가
        if where_clause:
            query += f" WHERE {where_clause}"

        # ORDER BY 절 추가
        if order_by:
            query += f" ORDER BY {order_by}"

        # LIMIT 및 OFFSET 추가
        if limit is not None:
            query += f" LIMIT {limit}"
            if offset is not None:
                query += f" OFFSET {offset}"

        cursor = await cls.execute_query(query, params, conn)
        rows = await cursor.fetchall()

        # 결과가 없으면 빈 리스트 반환
        if not rows:
            return []

        # 튜플 결과를 딕셔너리로 변환 (첫 번째 결과가 딕셔너리가 아닌 경우)
        if rows and not isinstance(rows[0], dict) and hasattr(cursor, 'description'):
            column_names = [column[0] for column in cursor.description]
            result_dicts = [dict(zip(column_names, row)) for row in rows]
            return [cls.model_class(**result_dict) for result_dict in result_dicts]
        else:
            # 이미 딕셔너리 형태인 경우
            return [cls.model_class(**row) for row in rows]

    @classmethod
    async def update(cls, id_value: int, update_data: Union[Dict, BaseModel], conn: Connection = None) -> bool:
        """레코드 업데이트"""
        # Dict 또는 BaseModel 타입 처리
        if isinstance(update_data, BaseModel):
            update_dict = update_data.dict(exclude_unset=True)
        else:
            update_dict = update_data

        # 업데이트할 필드가 없으면 True 반환
        if not update_dict:
            return True

        # 업데이트 쿼리 구성
        set_clause = ", ".join(f"{key} = %s" for key in update_dict.keys())
        values = list(update_dict.values())
        values.append(id_value)  # WHERE 절의 ID 값

        query = f"UPDATE {cls.table_name} SET {set_clause} WHERE {cls.id_column} = %s"

        cursor = await cls.execute_query(query, tuple(values), conn)
        return cursor.rowcount > 0

    @classmethod
    async def delete(cls, id_value: int, conn: Connection = None) -> bool:
        """레코드 삭제"""
        query = f"DELETE FROM {cls.table_name} WHERE {cls.id_column} = %s"

        cursor = await cls.execute_query(query, (id_value,), conn)
        return cursor.rowcount > 0

    @classmethod
    async def count(cls, where_clause: str = "", params: tuple = None, conn: Connection = None) -> int:
        """조건에 맞는 레코드 수 조회"""
        query = f"SELECT COUNT(*) as count FROM {cls.table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        cursor = await cls.execute_query(query, params, conn)
        result = await cursor.fetchone()

        return result["count"] if result else 0