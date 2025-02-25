# app/core/database.py
import asyncmy
import asyncmy.cursors
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# MySQL 연결 풀
mysql_pool = None


async def get_mysql_pool():
    """MySQL 연결 풀 가져오기"""
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
                cursorclass=asyncmy.cursors.DictCursor,
                autocommit=True,
            )
            logger.info("MySQL 연결 풀이 성공적으로 생성되었습니다! 🎯")
        except Exception as e:
            logger.error(f"MySQL 연결 풀 생성 오류: {e}")
            raise
    return mysql_pool


async def get_mysql_connection():
    """MySQL 연결 가져오기"""
    pool = await get_mysql_pool()
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)


async def close_db_connections():
    """모든 데이터베이스 연결 닫기"""
    global mysql_pool

    # MySQL 연결 풀 닫기
    if mysql_pool:
        mysql_pool.close()
        await mysql_pool.wait_closed()
        logger.info("MySQL 연결 풀이 성공적으로 닫혔습니다.")