from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.calendar import CalendarPostResponse
from app.services.calendar_service import CalendarService


router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"],
)


calendar_service = CalendarService()


@router.get(
    "/",
    response_model=list[CalendarPostResponse],
)
def get_calendar_posts(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return calendar_service.get_calendar_posts(
        db=db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )