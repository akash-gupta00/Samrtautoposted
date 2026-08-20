from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


analytics_service = AnalyticsService()


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_summary(
        db=db,
        current_user=current_user,
    )