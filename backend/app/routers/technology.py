import math
from fastapi import APIRouter, Depends, Query, Response
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.technology import TechnologyService
from backend.app.dependencies import get_pagination_params
from backend.app.schemas.common import ResponseEnvelope, PaginationMetadata
from backend.app.schemas.analytics import TechnologyAnalyticsOut

router = APIRouter(prefix="/technology", tags=["Technology"])

@router.get(
    "",
    response_model=ResponseEnvelope[list[TechnologyAnalyticsOut]],
    summary="Get Tech Stack Analytics",
    description="Returns a paginated list of technology tags and tools, sorted by hiring demand or salary levels."
)
def get_technology(
    response: Response,
    pagination: tuple[int, int] = Depends(get_pagination_params),
    sort_by: str = Query("job_demand_count", description="Field to sort by (e.g. tech_tag, job_demand_count, top_company)."),
    sort_order: str = Query("desc", description="Sort direction (asc or desc)."),
    search: str | None = Query(None, description="Filter tech tag by partial search query."),
    db=Depends(get_db)
):
    # Configure cache headers using settings max age configurations
    response.headers["Cache-Control"] = f"public, max-age={settings.CACHE_MAX_AGE_ANALYTICS}"
    page, page_size = pagination
    records, total_records = TechnologyService.get_technology_analytics(
        db, page=page, page_size=page_size, sort_by=sort_by,
        sort_order=sort_order, search=search
    )
    
    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 0
    pagination_meta = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_records=total_records,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )
    return ResponseEnvelope(data=records, metadata=pagination_meta)
