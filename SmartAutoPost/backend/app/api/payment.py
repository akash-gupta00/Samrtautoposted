from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.payment_service import PaymentService


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


payment_service = PaymentService()


@router.post(
    "/",
    response_model=PaymentResponse,
)
def create_payment(
    payment_data: PaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return payment_service.create_payment(
        db=db,
        payment_data=payment_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/",
    response_model=list[PaymentResponse],
)
def list_payments(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return payment_service.list_payments(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return payment_service.get_payment(
        db=db,
        payment_id=payment_id,
        current_user=current_user,
    )