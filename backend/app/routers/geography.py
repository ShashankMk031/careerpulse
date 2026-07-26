from fastapi import APIRouter, Depends, Query
from backend.app.database import get_db
from backend.app.services.geography import GeographyService
from backend.app.schemas.common import ResponseEnvelope
from backend.app.schemas.analytics import GeographyAnalyticsOut

router = APIRouter(prefix="/geography", tags=["Geography"])

@router.get(
    "",
    response_model=ResponseEnvelope[list[GeographyAnalyticsOut]],
    summary="Get Geographical job density",
    description="Returns geographical job concentrations, supporting country filters, remote filters, and sorting."
)
def get_geography(
    country: str | None = Query(None, description="Filter results by specific country match."),
    remote: bool | None = Query(None, description="True filters only remote zones, False filters only physical locations."),
    sort_by: str = Query("jobs_count", description="Field to sort by (e.g. country, region, jobs_count, company_count)."),
    sort_order: str = Query("desc", description="Sort direction (asc or desc)."),
    db=Depends(get_db)
):
    records = GeographyService.get_geography_stats(
        db, country=country, remote=remote, sort_by=sort_by, sort_order=sort_order
    )
    return ResponseEnvelope(data=records)
