# List type import kar rahe hain.
# Iska use recent posts aur activity list response me hoga.
from typing import List

# FastAPI ke required tools import kar rahe hain.
from fastapi import APIRouter, Depends, HTTPException

# SQLAlchemy database session type import kar rahe hain.
from sqlalchemy.orm import Session

# Database session dependency import kar rahe hain.
from app.database.session import get_db

# Current logged-in user verify karne wali dependency import kar rahe hain.
from app.dependencies.auth import get_current_user

# User model import kar rahe hain.
from app.models.user import User

# Dashboard ke saare response schemas import kar rahe hain.
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DashboardRecentPostResponse,
    DashboardActivityResponse,
    DashboardChartsResponse,
)

# Dashboard business logic service import kar rahe hain.
from app.services.dashboard_service import DashboardService


# Dashboard router create kar rahe hain.
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# Dashboard summary API.
@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary(
    # Organization ID query parameter se aayega.
    organization_id: int,

    # Database session dependency.
    db: Session = Depends(get_db),

    # Logged-in user dependency.
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard ke summary cards ka data return karega.
    """

    # Organization ID validate kar rahe hain.
    if organization_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Valid organization ID is required",
        )

    # Dashboard service se summary data le rahe hain.
    summary = DashboardService.get_summary(
        db=db,
        organization_id=organization_id,
    )

    # Summary response return kar rahe hain.
    return summary


# Dashboard recent posts API.
@router.get(
    "/recent-posts",
    response_model=List[DashboardRecentPostResponse],
)
def get_dashboard_recent_posts(
    # Organization ID query parameter se aayega.
    organization_id: int,

    # Default 5 latest posts return honge.
    limit: int = 5,

    # Database session dependency.
    db: Session = Depends(get_db),

    # Logged-in user dependency.
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard ke liye organization ke latest posts return karega.
    """

    # Organization ID validate kar rahe hain.
    if organization_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Valid organization ID is required",
        )

    # Limit minimum 1 hona chahiye.
    if limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Limit must be greater than 0",
        )

    # Maximum 20 posts return karne denge.
    if limit > 20:
        limit = 20

    # Dashboard service se latest posts le rahe hain.
    recent_posts = DashboardService.get_recent_posts(
        db=db,
        organization_id=organization_id,
        limit=limit,
    )

    # Recent posts ki list return kar rahe hain.
    return recent_posts


# Dashboard recent activity API.
@router.get(
    "/activity",
    response_model=List[DashboardActivityResponse],
)
def get_dashboard_activity(
    # Organization ID query parameter se aayega.
    organization_id: int,

    # Default 10 activities return hongi.
    limit: int = 10,

    # Database session dependency.
    db: Session = Depends(get_db),

    # Logged-in user dependency.
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard ki latest activities return karega.
    """

    # Organization ID validate kar rahe hain.
    if organization_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Valid organization ID is required",
        )

    # Limit minimum 1 hona chahiye.
    if limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Limit must be greater than 0",
        )

    # Maximum 50 activity records return karenge.
    if limit > 50:
        limit = 50

    # Dashboard service se recent activity le rahe hain.
    activities = DashboardService.get_recent_activity(
        db=db,
        organization_id=organization_id,
        limit=limit,
    )

    # Activities ki list return kar rahe hain.
    return activities


# Dashboard charts API.
@router.get(
    "/charts",
    response_model=DashboardChartsResponse,
)
def get_dashboard_charts(
    # Organization ID query parameter se aayega.
    organization_id: int,

    # Database session dependency.
    db: Session = Depends(get_db),

    # Logged-in user dependency.
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard charts ke liye status aur platform-wise data return karega.
    """

    # Organization ID validate kar rahe hain.
    if organization_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Valid organization ID is required",
        )

    # Dashboard service se chart data le rahe hain.
    charts = DashboardService.get_dashboard_charts(
        db=db,
        organization_id=organization_id,
    )

    # Chart response return kar rahe hain.
    return charts