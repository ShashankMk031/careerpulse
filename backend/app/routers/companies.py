import math
from fastapi import APIRouter, Depends, Query
from backend.app.database import get_db
from backend.app.services.companies import CompaniesService
from backend.app.dependencies import get_pagination_params
from backend.app.schemas.common import ResponseEnvelope, PaginationMetadata
from backend.app.schemas.analytics import CompanyAnalyticsOut

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get(
    "",
    response_model=ResponseEnvelope[list[CompanyAnalyticsOut]],
    summary="Get Active Companies list",
    description="Returns a paginated list of companies active in hiring, supporting search, min jobs filters, and sorting."
)
def get_companies(
    pagination: tuple[int, int] = Depends(get_pagination_params),
    sort_by: str = Query("company", description="Field to sort by (e.g. company, total_jobs, unique_locations, latest_posting)."),
    sort_order: str = Query("asc", description="Sort direction (asc or desc)."),
    search: str | None = Query(None, description="Filter companies by name search pattern."),
    min_jobs: int | None = Query(None, description="Filter companies with at least this number of job postings."),
    db=Depends(get_db)
):
    page, page_size = pagination
    records, total_records = CompaniesService.get_companies(
        db, page=page, page_size=page_size, sort_by=sort_by,
        sort_order=sort_order, search=search, min_jobs=min_jobs
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

@router.get(
    "/{company}",
    response_model=ResponseEnvelope[CompanyAnalyticsOut],
    summary="Get Single Company details",
    description="Retrieves granular metrics for a specific hiring company by name."
)
def get_company(company: str, db=Depends(get_db)):
    record = CompaniesService.get_company_by_name(db, company)
    return ResponseEnvelope(data=record)
