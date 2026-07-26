from fastapi import Query
from backend.app.exceptions import ValidationException

def get_pagination_params(
    page: int = Query(1, ge=1, description="Page index (starting from 1)."),
    page_size: int = Query(20, ge=1, le=100, description="Number of records to return per page (max 100).")
) -> tuple[int, int]:
    """
    FastAPI dependency validating and returning (page, page_size) tuple.
    """
    if page < 1:
        raise ValidationException("Page number must be >= 1.")
    if page_size < 1 or page_size > 100:
        raise ValidationException("Page size must be between 1 and 100.")
    return page, page_size
