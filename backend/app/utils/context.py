import time
from functools import wraps
from contextvars import ContextVar

# Context variable tracking current request correlation identifier
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="unknown")

# Context variable accumulating database statement durations in milliseconds
db_duration_ctx: ContextVar[float] = ContextVar("db_duration", default=0.0)

def track_db_time(func):
    """
    Decorator measuring duration of database calls and accumulating it in db_duration_ctx.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000.0
            db_duration_ctx.set(db_duration_ctx.get() + elapsed)
    return wrapper
