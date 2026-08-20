from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorResponse,
    CompetitorUpdate,
)

from app.services.competitor_service import CompetitorService


router = APIRouter(
    prefix="/competitors",
    tags=["Competitors"],
)

competitor_service = CompetitorService()


@router.post(
    "",
    response_model=CompetitorResponse,
    status_code=201,
)
def create_competitor(
    competitor_data: CompetitorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Naya competitor create karega.
    """

    return competitor_service.create_competitor(
        db=db,
        competitor_data=competitor_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "",
    response_model=list[CompetitorResponse],
)
def list_competitors(
    organization_id: int,
    platform: str | None = None,
    status: str | None = None,
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
    """
    Organization ke competitors ki list return karega.
    """

    return competitor_service.list_competitors(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
        platform=platform,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{competitor_id}",
    response_model=CompetitorResponse,
)
def get_competitor(
    competitor_id: int,
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Competitor ki complete detail return karega.
    """

    return competitor_service.get_competitor(
        db=db,
        competitor_id=competitor_id,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.put(
    "/{competitor_id}",
    response_model=CompetitorResponse,
)
def update_competitor(
    competitor_id: int,
    organization_id: int,
    competitor_data: CompetitorUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Existing competitor update karega.
    """

    return competitor_service.update_competitor(
        db=db,
        competitor_id=competitor_id,
        organization_id=organization_id,
        competitor_data=competitor_data,
        current_user=current_user,
        request=request,
    )


@router.delete(
    "/{competitor_id}",
)
def delete_competitor(
    competitor_id: int,
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Competitor delete karega.
    """

    return competitor_service.delete_competitor(
        db=db,
        competitor_id=competitor_id,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )