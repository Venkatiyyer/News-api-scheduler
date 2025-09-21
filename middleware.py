import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from fastapi import Request
from logger import logger


class TotalTimeMiddleware(BaseHTTPMiddleware):
    """
    Measures total request time (ms) and injects "total_time_taken" into JSON responses.

    Behavior:
    - JSON dicts: adds total_time_taken at top-level.
    - JSON lists/scalars: wraps as { "data": <payload>, "total_time_taken": <ms> }.
    - Non-JSON responses are left untouched, but X-Response-Time-ms header is added.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception as e:
            logger.exception(f"Exception during request processing: {e}")
            raise

        total_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Response-Time-ms"] = str(total_ms)

        content_type = getattr(response, "media_type", "") or response.headers.get("content-type", "")

        if content_type.startswith("application/json"):
            body_bytes = b""
            try:
                # Prefer .body if available
                if hasattr(response, "body") and response.body is not None:
                    body_bytes = response.body
                else:
                    async for chunk in response.body_iterator:
                        body_bytes += chunk
            except Exception as e:
                logger.exception(f"Failed to read response body for timing injection: {e}")
                return response

            if not body_bytes:
                return response

            try:
                payload = json.loads(body_bytes.decode())
            except Exception as e:
                logger.warning(f"Response body not JSON despite content-type: {e}")
                return response

            # Inject timing
            if isinstance(payload, dict):
                payload["total_time_taken"] = total_ms
                new_payload = payload
            else:
                new_payload = {"data": payload, "total_time_taken": total_ms}

            # Preserve headers (except content-length)
            headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
            logger.info(f"Injected total_time_taken: {total_ms}ms for path {request.url.path}")
            return JSONResponse(new_payload, status_code=response.status_code, headers=headers)

        # Non-JSON responses: just return with header
        return response
