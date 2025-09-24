import os
import ssl
import asyncio
import aiomysql
from urllib.parse import urlparse
from dotenv import load_dotenv
from logger import logger

load_dotenv()


class AsyncMySQLConnector:
    """
    Asynchronous MySQL connector using aiomysql connection pool with SSL.
    """
    _pool = None

    @classmethod
    async def init_pool(cls):
        if cls._pool:
            return

        db_url = os.getenv("DB_URL")
        if not db_url:
            logger.error("DB_URL is not set in environment")
            raise RuntimeError("DB_URL is not set in environment")

        parsed = urlparse(db_url)
        ca_path = os.getenv("DB_CA_PATH", "isrgrootx1.pem")

        try:
            ssl_ctx = ssl.create_default_context(cafile=ca_path)
            ssl_ctx.check_hostname = True
            ssl_ctx.verify_mode = ssl.CERT_REQUIRED

            cls._pool = await aiomysql.create_pool(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                db=parsed.path.lstrip("/"),
                ssl=ssl_ctx,
                autocommit=True,
                minsize=1,
                maxsize=10,
            )
            logger.info("MySQL connection pool initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize MySQL pool: {e}")
            raise

    @classmethod
    async def insert_news(cls, title: str, description: str):
        query = "INSERT INTO news (title, description) VALUES (%s, %s)"
        return await cls.execute_query(query, (title, description), fetch=False)
    
    @classmethod
    async def delete_news(cls, title: str, description: str):
        query = "DELETE FROM news  WHERE DATE(`published_at`) = %s"
        return await cls.execute_query(query, (title, description), fetch=False)

    @classmethod
    async def execute_query(cls, query: str, params: tuple = None, fetch: bool = True):
        if cls._pool is None:
            await cls.init_pool()

        try:
            async with cls._pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params or ())
                    if fetch:
                        rows = await cur.fetchall()
                        logger.debug(f"Query executed successfully: {query} | rows={len(rows)}")
                        return rows
                    else:
                        rowcount = cur.rowcount
                        logger.debug(f"Query executed successfully: {query} | affected={rowcount}")
                        return rowcount
        except Exception as e:
            logger.exception(f"Error executing query: {query} | params={params} | error={e}")
            return [] if fetch else 0

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            try:
                cls._pool.close()
                await cls._pool.wait_closed()
                logger.info("MySQL connection pool closed")
            except Exception as e:
                logger.warning(f"Error while closing MySQL pool: {e}")
            finally:
                cls._pool = None


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def _test():
        await AsyncMySQLConnector.init_pool()
        query = """
            SELECT `id`, `title`, `description`, `published_at`
            FROM `news`
            WHERE DATE(`published_at`) = '2025-09-21'
        """
        rows = await AsyncMySQLConnector.execute_query(query, fetch=True)
        print("Sample rows ->", rows)
        await AsyncMySQLConnector.close_pool()

    asyncio.run(_test())
