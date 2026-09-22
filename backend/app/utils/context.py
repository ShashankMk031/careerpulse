import time
import inspect
import threading
from functools import wraps
from contextvars import ContextVar

# Context variable tracking current request correlation identifier
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="unknown")

class DBTimingAccumulator:
    """
    Request-scoped mutable accumulator for tracking database execution duration.
    Using a mutable container ensures that modifications made in worker threads
    (via run_in_threadpool) remain visible across context boundaries.
    """
    def __init__(self) -> None:
        self.duration_ms: float = 0.0
        self.call_count: int = 0
        self.initialized: bool = False
        self._lock = threading.Lock()

    def add(self, elapsed_ms: float) -> None:
        with self._lock:
            self.duration_ms += elapsed_ms
            self.call_count += 1

    def reset(self) -> None:
        with self._lock:
            self.duration_ms = 0.0
            self.call_count = 0
            self.initialized = True

    def get_duration(self) -> float:
        with self._lock:
            return self.duration_ms

    def __float__(self) -> float:
        return self.get_duration()

    def __format__(self, format_spec: str) -> str:
        return format(self.get_duration(), format_spec)

    def __round__(self, ndigits: int = 0) -> float:
        return round(self.get_duration(), ndigits)

    def __repr__(self) -> str:
        return f"<DBTimingAccumulator: {self.get_duration():.2f}ms, calls={self.call_count}>"

# Context variable accumulating database statement durations via mutable accumulator
db_timing_ctx: ContextVar[DBTimingAccumulator | None] = ContextVar("db_timing", default=None)

def get_or_create_db_timing() -> DBTimingAccumulator:
    """
    Retrieves the current request's DBTimingAccumulator, creating one if not present.
    """
    acc = db_timing_ctx.get()
    if acc is None:
        acc = DBTimingAccumulator()
        db_timing_ctx.set(acc)
    return acc

def get_db_duration() -> float:
    """
    Returns accumulated database duration in milliseconds for the current request.
    """
    acc = db_timing_ctx.get()
    return acc.get_duration() if acc is not None else 0.0

def reset_db_timing() -> DBTimingAccumulator:
    """
    Resets the database timing accumulator for the current request.
    """
    acc = get_or_create_db_timing()
    acc.reset()
    return acc

class _DBDurationProxy:
    """
    Backwards-compatible proxy for db_duration_ctx.
    Allows .get() to return the float duration and .set(...) to update the accumulator.
    """
    def get(self, default: float = 0.0) -> float:
        acc = db_timing_ctx.get()
        return acc.get_duration() if acc is not None else default

    def set(self, value) -> None:
        if isinstance(value, DBTimingAccumulator):
            db_timing_ctx.set(value)
            return
        acc = get_or_create_db_timing()
        if isinstance(value, (int, float)):
            acc.duration_ms = float(value)
            acc.initialized = True

db_duration_ctx = _DBDurationProxy()

def track_db_time(func):
    """
    Decorator measuring duration of database calls and accumulating it in the request-scoped accumulator.
    """
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - start) * 1000.0
                acc = get_or_create_db_timing()
                acc.add(elapsed)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - start) * 1000.0
                acc = get_or_create_db_timing()
                acc.add(elapsed)
        return sync_wrapper

