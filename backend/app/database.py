from backend.database.pool import get_pooled_connection
from backend.app.utils.context import db_timing_ctx, get_or_create_db_timing

def get_db():
    """
    FastAPI dependency yielding a pooled PostgreSQL connection.
    Exposes clean transaction commit and rollback capabilities via context managers.
    """
    # Ensure database timing accumulator is initialized/reset exactly once per request
    timing = db_timing_ctx.get()
    if timing is None:
        timing = get_or_create_db_timing()
        timing.reset()
    elif not timing.initialized:
        timing.reset()

    with get_pooled_connection() as conn:
        yield conn

