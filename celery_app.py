import os
import asyncio
from dotenv import load_dotenv
from celery import Celery
from logger import logger

load_dotenv()

# Handle Windows event loop policy for aiomysql
if os.name == "nt":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logger.info("Windows event loop policy set successfully")
    except Exception as e:
        logger.warning(f"Failed to set Windows event loop policy: {e}")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery configuration
try:
    celery_app = Celery(
        "tasks",
        broker="amqp://guest:guest@localhost//",  # RabbitMQ default
        backend="rpc://",                         # optional result backend
    )
    logger.info("Celery app initialized with RabbitMQ broker and RPC backend")
except Exception as e:
    logger.exception(f"Failed to initialize Celery app: {e}")
    raise

# Beat schedule: run fetch_news every 60s
celery_app.conf.beat_schedule = {
    "fetch-news-every-minute": {
        "task": "scheduler.fetch_news",
        "schedule": 60.0,  # seconds
    },
}
logger.info("Celery beat schedule configured: fetch_news every 60s")

# Autodiscover tasks in the scheduler module
celery_app.autodiscover_tasks(["scheduler"])
logger.info("Celery configured to autodiscover tasks in 'scheduler' package")

# Explicit import so tasks are registered
try:
    import scheduler  # noqa
    logger.info("Scheduler module imported successfully")
except ImportError as e:
    logger.exception(f"Failed to import scheduler module: {e}")
    raise
