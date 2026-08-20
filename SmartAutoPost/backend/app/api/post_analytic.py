from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.post_analytic import (
    PostAnalyticCreate,
    PostAnalyticResponse,
    PostAnalyticUpdate,
)
from app.services.post_analytic_service import PostAnalyticService


router = APIRouter(
    prefix="/post-analytics",
    tags=["Post Analytics"],
)

post_analytic_service = PostAnalyticService()


@router.post(
    "",
    response_model=PostAnalyticResponse,
    status_code=201,
)
def create_post_analytic(
    analytic_data: PostAnalyticCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Naya post analytic record create karega.
    """

    return post_analytic_service.create_analytic(
        db=db,
        analytic_data=analytic_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "",
    response_model=list[PostAnalyticResponse],
)
def list_post_analytics(
    post_id: int,
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
    Kisi post ke saare analytic records return karega.
    """

    return post_analytic_service.list_analytics(
        db=db,
        post_id=post_id,
        current_user=current_user,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{analytic_id}",
    response_model=PostAnalyticResponse,
)
def get_post_analytic(
    analytic_id: int,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ek particular post analytic record return karega.
    """

    return post_analytic_service.get_analytic(
        db=db,
        analytic_id=analytic_id,
        post_id=post_id,
        current_user=current_user,
    )


@router.put(
    "/{analytic_id}",
    response_model=PostAnalyticResponse,
)
def update_post_analytic(
    analytic_id: int,
    post_id: int,
    analytic_data: PostAnalyticUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Existing post analytic record update karega.
    """

    return post_analytic_service.update_analytic(
        db=db,
        analytic_id=analytic_id,
        post_id=post_id,
        analytic_data=analytic_data,
        current_user=current_user,
        request=request,
    )


@router.delete(
    "/{analytic_id}",
)
def delete_post_analytic(
    analytic_id: int,
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Post analytic record delete karega.
    """

    return post_analytic_service.delete_analytic(
        db=db,
        analytic_id=analytic_id,
        post_id=post_id,
        current_user=current_user,
        request=request,
    )