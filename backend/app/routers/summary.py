from fastapi import APIRouter, Depends, Response
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services.summary import SummaryService
from backend.app.schemas.common import ResponseEnvelope
from backend.app.schemas.analytics import HiringSummaryOut

router = APIRouter(prefix="/summary", tags=["Summary"])

@router.get(
    "",
    response_model=ResponseEnvelope[HiringSummaryOut],
    summary="Get Dashboard KPIs",
    description="Returns the latest global hiring analytics KPIs, including jobs counts, salaries, and top tags."
)
def get_summary(response: Response, db=Depends(get_db)):
    # Configure cache headers using settings max age configurations
    response.headers["Cache-Control"] = f"public, max-age={settings.CACHE_MAX_AGE_SUMMARY}"
    summary_data = SummaryService.get_dashboard_summary(db)
    return ResponseEnvelope(data=summary_data)
