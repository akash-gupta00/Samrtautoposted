from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.competitor_metric import (
    CompetitorMetricCreate,
    CompetitorMetricUpdate,
    CompetitorMetricResponse,
)

from app.services.competitor_metric_service import (
    CompetitorMetricService,
)


router = APIRouter(
    prefix="/competitor-metrics",
    tags=["Competitor Metrics"],
)

competitor_metric_service = CompetitorMetricService()


@router.post(
    "",
    response_model=CompetitorMetricResponse,
    status_code=201,
)
def create_metric(
    metric_data: CompetitorMetricCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return competitor_metric_service.create_metric(
        db=db,
        metric_data=metric_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "",
    response_model=list[CompetitorMetricResponse],
)
def list_metrics(
    competitor_id: int,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return competitor_metric_service.list_metrics(
        db=db,
        competitor_id=competitor_id,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{metric_id}",
    response_model=CompetitorMetricResponse,
)
def get_metric(
    metric_id: int,
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return competitor_metric_service.get_metric(
        db=db,
        metric_id=metric_id,
        competitor_id=competitor_id,
        current_user=current_user,
    )


@router.put(
    "/{metric_id}",
    response_model=CompetitorMetricResponse,
)
def update_metric(
    metric_id: int,
    competitor_id: int,
    metric_data: CompetitorMetricUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return competitor_metric_service.update_metric(
        db=db,
        metric_id=metric_id,
        competitor_id=competitor_id,
        metric_data=metric_data,
        current_user=current_user,
        request=request,
    )


@router.delete(
    "/{metric_id}",
)
def delete_metric(
    metric_id: int,
    competitor_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return competitor_metric_service.delete_metric(
        db=db,
        metric_id=metric_id,
        competitor_id=competitor_id,
        current_user=current_user,
        request=request,
    )