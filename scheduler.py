import os
import asyncio
import requests
from dotenv import load_dotenv
from celery_app import celery_app
from connector import AsyncMySQLConnector
from logger import logger

load_dotenv()

API_KEY = os.getenv("NEWS_API")  # changed to uppercase for convention
URL = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}"


@celery_app.task(name="scheduler.fetch_news")
def fetch_news():
    logger.info("Task [fetch_news] started")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _fetch():
        try:
            logger.info("Fetching news from NewsAPI...")
            response = requests.get(URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles", [])
            logger.info(f"Fetched {len(articles)} articles from API")

            inserted_count = 0
            for article in articles:
                title = article.get("title")
                description = article.get("description")
                if title:  # title is mandatory
                    await AsyncMySQLConnector.insert_news(title, description)
                    inserted_count += 1

            logger.info(f"Inserted {inserted_count} articles into DB")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in async fetch: {e}")
            raise

    try:
        loop.run_until_complete(_fetch())
    except Exception as e:
        logger.error(f"Task [fetch_news] failed: {e}")
    finally:
        loop.close()
        logger.info("Task [fetch_news] finished")
