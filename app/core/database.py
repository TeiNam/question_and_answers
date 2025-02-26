# app/core/database.py
import asyncmy
import logging
from app.core.config import settings
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# MySQL 연결 풀
mysql_pool = None


async def init_db_pool():
    """MySQL 연결 풀 초기화"""
    global mysql_pool
    if mysql_pool is None:
        try:
            mysql_pool = await asyncmy.create_pool(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                db=settings.MYSQL_DB,
                charset="utf8mb4",
                autocommit=True,
            )
            logger.info("MySQL 연결 풀이 성공적으로 생성되었습니다! 🎯")
        except Exception as e:
            logger.error(f"MySQL 연결 풀 생성 오류: {e}")
            raise


async def get_db():
    """FastAPI 의존성 주입을 위한 데이터베이스 연결 제공자"""
    global mysql_pool
    if mysql_pool is None:
        await init_db_pool()

    conn = await mysql_pool.acquire()
    try:
        yield conn
    finally:
        await mysql_pool.release(conn)


@asynccontextmanager
async def transaction():
    """데이터베이스 트랜잭션 컨텍스트 매니저"""
    global mysql_pool
    if mysql_pool is None:
        await init_db_pool()

    conn = await mysql_pool.acquire()
    try:
        await conn.begin()
        yield conn
        await conn.commit()
    except Exception as e:
        await conn.rollback()
        raise e
    finally:
        await mysql_pool.release(conn)


async def close_db_connections():
    """모든 데이터베이스 연결 닫기"""
    global mysql_pool

    # MySQL 연결 풀 닫기
    if mysql_pool:
        mysql_pool.close()
        await mysql_pool.wait_closed()
        logger.info("MySQL 연결 풀이 성공적으로 닫혔습니다.")