from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.social_account import (
    SocialAccountCreate,
    SocialAccountResponse,
)

from app.services.social_account_service import SocialAccountService


router = APIRouter(
    prefix="/social-accounts",
    tags=["Social Accounts"],
)


social_account_service = SocialAccountService()


@router.post(
    "/",
    response_model=SocialAccountResponse,
)
def connect_social_account(
    data: SocialAccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return social_account_service.connect_account(
        db=db,
        data=data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/",
    response_model=list[SocialAccountResponse],
)
def list_social_accounts(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return social_account_service.list_accounts(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.delete("/{account_id}")
def delete_social_account(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return social_account_service.delete_account(
        db=db,
        account_id=account_id,
        current_user=current_user,
        request=request,
    )