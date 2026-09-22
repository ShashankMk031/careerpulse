import time
import uuid
import json
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.app.utils.context import (
    request_id_ctx,
    db_timing_ctx,
    DBTimingAccumulator,
)

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
        token_req = request_id_ctx.set(request_id)
        
        # Initialize request-scoped mutable DB timing accumulator
        timing_acc = DBTimingAccumulator()
        request.state.db_timing = timing_acc
        token_db = db_timing_ctx.set(timing_acc)
        
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            response = await call_next(request)
            
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            db_duration = timing_acc.get_duration()
            
            # Inject custom tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"
            response.headers["X-Database-Time-MS"] = f"{db_duration:.2f}"
            
            duration_val = round(duration_ms, 2)
            db_val = round(db_duration, 2)
            api_val = round(max(0.0, duration_val - db_val), 2)

            # Structured terminal JSON log
            log_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "client_ip": client_ip,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration": duration_val,
                "database_duration": db_val,
                "api_duration": api_val
            }
            print(json.dumps(log_record))
            
            return response
        finally:
            db_timing_ctx.reset(token_db)
            request_id_ctx.reset(token_req)

