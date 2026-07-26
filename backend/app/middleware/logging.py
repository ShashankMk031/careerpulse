import time
import uuid
import json
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.app.utils.context import request_id_ctx, db_duration_ctx

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Intercepts incoming HTTP requests, generates unique request IDs,
        measures execution durations, tracks database transaction times,
        and logs transaction outcomes in a structured JSON format.
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Correlate request_id in contextvar
        request_id_ctx.set(request_id)
        
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        
        response = await call_next(request)
        
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        db_duration = db_duration_ctx.get()
        
        # Inject custom tracking headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"
        response.headers["X-Database-Time-MS"] = f"{db_duration:.2f}"
        
        # Structured terminal JSON log
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": round(duration_ms, 2),
            "database_duration": round(db_duration, 2),
            "api_duration": round(max(0.0, duration_ms - db_duration), 2)
        }
        print(json.dumps(log_record))
        
        return response
