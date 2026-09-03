from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.refund import RefundCreate, RefundResponse
from app.services.refund_service import RefundService


router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"],
)

refund_service = RefundService()


@router.post(
    "/",
    response_model=RefundResponse,
)
def create_refund(
    refund_data: RefundCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return refund_service.create_refund(
        db=db,
        payment_id=refund_data.payment_id,
        amount=refund_data.amount,
        reason=refund_data.reason,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/",
    response_model=list[RefundResponse],
)
def list_refunds(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return refund_service.list_refunds(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.get(
    "/{refund_id}",
    response_model=RefundResponse,
)
def get_refund(
    refund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return refund_service.get_refund(
        db=db,
        refund_id=refund_id,
        current_user=current_user,
    )