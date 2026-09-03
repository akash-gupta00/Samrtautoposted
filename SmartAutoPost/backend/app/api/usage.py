from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.usage_service import UsageService


router = APIRouter(
    prefix="/usage",
    tags=["Usage"],
)

usage_service = UsageService()


@router.get("/summary")
def get_usage_summary(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return usage_service.get_usage_summary(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.get("/{usage_type}")
def get_usage_detail(
    usage_type: str,
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return usage_service.get_remaining_usage(
        db=db,
        organization_id=organization_id,
        usage_type=usage_type,
        current_user=current_user,
    )


@router.post("/{usage_type}/increment")
def increment_usage(
    usage_type: str,
    organization_id: int,
    request: Request,
    increment_by: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage = usage_service.increment_usage(
        db=db,
        organization_id=organization_id,
        usage_type=usage_type,
        increment_by=increment_by,
        current_user=current_user,
        request=request,
    )

    return {
        "message": "Usage updated successfully",
        "organization_id": usage.organization_id,
        "usage_type": usage.usage_type,
        "usage_count": usage.usage_count,
        "period_start": usage.period_start,
        "period_end": usage.period_end,
    }