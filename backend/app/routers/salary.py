from fastapi import APIRouter, Depends
from backend.app.database import get_db
from backend.app.services.salary import SalaryService
from backend.app.schemas.common import ResponseEnvelope
from backend.app.schemas.analytics import SalaryAnalyticsOut

router = APIRouter(prefix="/salary", tags=["Salary"])

@router.get(
    "",
    response_model=ResponseEnvelope[list[SalaryAnalyticsOut]],
    summary="Get Salary Tier distribution",
    description="Returns aggregate statistics of job postings categorized by standard salary bracket tiers."
)
def get_salary_tiers(db=Depends(get_db)):
    records = SalaryService.get_salary_tiers(db)
    return ResponseEnvelope(data=records)
