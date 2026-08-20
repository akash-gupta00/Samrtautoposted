from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


subscription_service = SubscriptionService()


@router.post(
    "/",
    response_model=SubscriptionResponse,
)
def create_subscription(
    subscription_data: SubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Nayi subscription create karega.
    """

    return subscription_service.create_subscription(
        db=db,
        subscription_data=subscription_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/current",
    response_model=SubscriptionResponse,
)
def get_current_subscription(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Organization ki active subscription return karega.
    """

    return subscription_service.get_current_subscription(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.get(
    "/history",
    response_model=list[SubscriptionResponse],
)
def get_subscription_history(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Organization ki subscription history return karega.
    """

    return subscription_service.list_subscriptions(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.delete(
    "/current",
    response_model=SubscriptionResponse,
)
def cancel_current_subscription(
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Current active subscription cancel karega.
    """

    return subscription_service.cancel_subscription(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
        request=request,
    )