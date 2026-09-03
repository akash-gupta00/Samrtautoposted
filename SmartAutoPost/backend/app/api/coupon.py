from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.coupon import (
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    CouponValidate,
    CouponValidationResponse,
)
from app.services.coupon_service import CouponService


router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"],
)

coupon_service = CouponService()


@router.post(
    "/",
    response_model=CouponResponse,
)
def create_coupon(
    coupon_data: CouponCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return coupon_service.create_coupon(
        db=db,
        coupon_data=coupon_data,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/",
    response_model=list[CouponResponse],
)
def list_coupons(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return coupon_service.list_coupons(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.post(
    "/validate",
    response_model=CouponValidationResponse,
)
def validate_coupon(
    coupon_data: CouponValidate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return coupon_service.validate_coupon(
        db=db,
        organization_id=coupon_data.organization_id,
        code=coupon_data.code,
        amount=coupon_data.amount,
        current_user=current_user,
        request=request,
    )


@router.get(
    "/{coupon_id}",
    response_model=CouponResponse,
)
def get_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return coupon_service.get_coupon(
        db=db,
        coupon_id=coupon_id,
        current_user=current_user,
    )


@router.put(
    "/{coupon_id}",
    response_model=CouponResponse,
)
def update_coupon(
    coupon_id: int,
    coupon_data: CouponUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return coupon_service.update_coupon(
        db=db,
        coupon_id=coupon_id,
        coupon_data=coupon_data,
        current_user=current_user,
        request=request,
    )


@router.delete("/{coupon_id}")
def delete_coupon(
    coupon_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return coupon_service.delete_coupon(
        db=db,
        coupon_id=coupon_id,
        current_user=current_user,
        request=request,
    )