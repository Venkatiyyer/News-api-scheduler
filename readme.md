# News Fetcher — FastAPI + Celery + MySQL

This repository implements a small project that fetches news from the NewsAPI and stores it into a MySQL database. A FastAPI service exposes an endpoint to query stored news by date. Celery runs a periodic task (configured to run every minute) that fetches news and inserts them into the database.

---

# Features

- FastAPI server with a `/news` endpoint: `GET /news?date=YYYY-MM-DD`.
- Celery task (`scheduler.fetch_news`) that calls NewsAPI and inserts articles into MySQL every minute.
- Async MySQL connection pool using `aiomysql`.
- Custom middleware that measures request time and injects `total_time_taken` (ms) into JSON responses.
- Centralized logging via `logger.py` (INFO/WARNING/ERROR levels).
- Minimal, pragmatic error handling for API and Celery task failures.

---

# Repository layout

- `main.py` — FastAPI app and `/news` endpoint.
- `logger.py` — central logging configuration.
- `middleware_timing_json.py` — middleware that injects `total_time_taken` into JSON responses.
- `connector.py` — `AsyncMySQLConnector` (aiomysql pool + helper methods).
- `celery_app.py` — Celery app configuration and beat schedule.
- `scheduler.py` — Celery task that fetches news and inserts into DB.
- `requirements.txt` — minimal dependencies.
- `README.md` — this file.

---

# Prerequisites

- Python 3.10+ (recommended to use latest stable Python)
- MySQL server
- RabbitMQ (default Celery broker in this project) or Redis if you change the broker
- NewsAPI API key (https://newsapi.org/)

---

# Setup

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and set environment variables. Example:

```
DB_URL=mysql://dbuser:dbpass@localhost:3306/newsdb
DB_CA_PATH=/path/to/isrgrootx1.pem       # optional (used for SSL)
NEWS_API=your_newsapi_api_key
REDIS_URL=redis://localhost:6379/0       # optional if you decide to use Redis
```

> Note: `DB_URL` should be a valid URL in the form: `mysql://user:pass@host:port/dbname`.

4. Create the `news` table in your MySQL database (example SQL):

```sql
CREATE TABLE news (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  published_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

If you plan to use Alembic for migrations, initialize and run migrations as usual:

```bash
alembic upgrade head
```

---

# Running the app locally

### Start FastAPI

```bash
uvicorn main:server --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/health` to check the service health.

### Start Celery worker and beat

This project configures Celery to use RabbitMQ by default (hardcoded broker). Start worker and beat in separate terminals:

```bash
# Start worker
celery -A celery_app.celery_app worker --loglevel=info

# Start beat scheduler
celery -A celery_app.celery_app beat --loglevel=info
```

If you switch to Redis (and update `celery_app.py` accordingly or use `celery[redis]`), you can set `broker` and `backend` via environment variables and use the same commands.

---

# API Usage

Fetch news stored for a given date (YYYY-MM-DD):

```bash
curl "http://localhost:8000/news?date=2025-09-21"
```

Successful JSON response will include `total_time_taken` (milliseconds) injected by the middleware. The `X-Response-Time-ms` header is also set for easy monitoring.

---

# Logging

All logging is centralized via `logger.py` and prints to stdout. Levels used:

- `INFO` — normal lifecycle events (startup, task start/finish, DB pool init)
- `WARNING` — recoverable issues
- `ERROR` / `EXCEPTION` — failures and stack traces

Check Celery worker logs and FastAPI logs for task and API-level information.

---

# Error handling & resilience

- Missing `DB_URL` raises a clear `RuntimeError` during pool initialization.
- Celery task logs and re-raises `requests` errors; unexpected exceptions are logged with stack traces.
- `execute_query` returns `[]` or `0` on failure to keep API responses consistent.
- Middleware will not modify non-JSON responses but still sets the timing header.

---

# Windows-specific notes

If you are running on Windows and using `aiomysql`, set the event loop policy before creating pools or running tasks. The code already attempts to set `asyncio.WindowsSelectorEventLoopPolicy()` where needed.

---

# Troubleshooting

- `aiomysql` connection issues: verify `DB_URL`, network connectivity, and SSL cert path (`DB_CA_PATH`) if used.
- Celery cannot connect to broker: ensure RabbitMQ is running and accessible at the configured URL.
- NewsAPI rate limits: NewsAPI may reject requests when you exceed its rate limit. Handle this by checking API responses and adding retries/backoff if needed.

---

# Extensibility ideas

- Make Celery broker/backend configurable via environment variables (switch between RabbitMQ and Redis).
- Add Alembic migrations for the `news` table and other schema changes.
- Add deduplication logic on insert (avoid inserting same article multiple times).
- Use an async HTTP client (e.g., `httpx`) and make the Celery task fully async.

---

# License

MIT

---

If you want any edits (more setup steps, additional commands, or to pin dependency versions), tell me and I will update the README.

