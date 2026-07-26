from backend.database.pool import get_pooled_connection
from backend.app.utils.context import db_duration_ctx

def get_db():
    """
    FastAPI dependency yielding a pooled PostgreSQL connection.
    Exposes clean transaction commit and rollback capabilities via context managers.
    """
    # Reset database query accumulation duration for the current request context
    db_duration_ctx.set(0.0)
    with get_pooled_connection() as conn:
        yield conn
