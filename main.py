import os
import asyncio
from fastapi import FastAPI, Query, HTTPException
from dotenv import load_dotenv
from middleware import TotalTimeMiddleware
from connector import AsyncMySQLConnector
from logger import logger  # import logger
from datetime import datetime

load_dotenv()

server = FastAPI()
server.add_middleware(TotalTimeMiddleware)


@server.get("/health")
def home():
    logger.info("Health check endpoint called")
    return {"message": "Hello, world!"}


@server.on_event("startup")
async def startup_event():
    try:
        await AsyncMySQLConnector.init_pool()
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing DB pool: {e}")


@server.get("/news")
async def get_news(date: str = Query(..., description="Date in YYYY-MM-DD format")):
    """
    Fetch news articles for a given date.
    Example: /news?date=2025-09-21
    """
    try:
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        query = """
            SELECT `id`, `title`, `description`, `published_at`
            FROM `news`
            WHERE DATE(`published_at`) = %s
            ORDER BY `published_at` DESC
        """
        rows = await AsyncMySQLConnector.execute_query(query, (date,), fetch=True)
        logger.info(f"Fetched {len(rows)} articles for date: {date}")
        return {"date": date, "articles": rows or []}

    except Exception as e:
        logger.exception(f"Failed to fetch news for date {date}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

    

@server.delete("/del_news")
async def delete_news():
    """
    Delete news for today.
    Example: /del_news
    """
    date = datetime.now().strftime("%Y-%m-%d")  # today's date
    try:
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        query = """
            DELETE FROM `news`
            WHERE DATE(`published_at`) = %s
        """
        await AsyncMySQLConnector.execute_query(query, (date,), fetch=False)
        logger.info(f"Deleted all news for date: {date}")
        return {"message": f"Deleted all news for date {date}"}

    except Exception as e:
        logger.exception(f"Failed to delete news for date {date}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
