from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.coupon import Coupon
from app.models.organization import Organization
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate
from app.schemas.coupon import CouponCreate, CouponUpdate

from app.services.audit_log_service import AuditLogService


class CouponService:

    def check_organization_access(
        self,
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        organization = (
            db.query(Organization)
            .filter(
                Organization.id == organization_id,
                Organization.owner_id == current_user.id,
            )
            .first()
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization not found or access denied",
            )

        return organization

    def create_coupon(
        self,
        db: Session,
        coupon_data: CouponCreate,
        current_user: User,
        request: Request,
    ):
        self.check_organization_access(
            db=db,
            organization_id=coupon_data.organization_id,
            current_user=current_user,
        )

        coupon_code = coupon_data.code.strip().upper()

        existing_coupon = (
            db.query(Coupon)
            .filter(Coupon.code == coupon_code)
            .first()
        )

        if existing_coupon:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Coupon already exists",
            )

        coupon = Coupon(
            organization_id=coupon_data.organization_id,
            code=coupon_code,
            description=coupon_data.description,
            discount_type=coupon_data.discount_type,
            discount_value=coupon_data.discount_value,
            minimum_amount=coupon_data.minimum_amount,
            max_discount=coupon_data.max_discount,
            usage_limit=coupon_data.usage_limit,
            expires_at=coupon_data.expires_at,
        )

        db.add(coupon)
        db.commit()
        db.refresh(coupon)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=coupon.organization_id,
                action="coupon_created",
                entity_type="coupon",
                entity_id=coupon.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "code": coupon.code,
                    "discount_type": coupon.discount_type,
                    "discount_value": str(coupon.discount_value),
                    "minimum_amount": str(coupon.minimum_amount),
                    "max_discount": (
                        str(coupon.max_discount)
                        if coupon.max_discount is not None
                        else None
                    ),
                    "usage_limit": coupon.usage_limit,
                    "is_active": coupon.is_active,
                    "expires_at": (
                        coupon.expires_at.isoformat()
                        if coupon.expires_at
                        else None
                    ),
                },
            ),
        )

        return coupon

    def list_coupons(
        self,
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        return (
            db.query(Coupon)
            .filter(
                Coupon.organization_id == organization_id
            )
            .order_by(Coupon.id.desc())
            .all()
        )

    def get_coupon(
        self,
        db: Session,
        coupon_id: int,
        current_user: User,
    ):
        coupon = (
            db.query(Coupon)
            .filter(Coupon.id == coupon_id)
            .first()
        )

        if not coupon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coupon not found",
            )

        self.check_organization_access(
            db=db,
            organization_id=coupon.organization_id,
            current_user=current_user,
        )

        return coupon

    def update_coupon(
        self,
        db: Session,
        coupon_id: int,
        coupon_data: CouponUpdate,
        current_user: User,
        request: Request,
    ):
        coupon = self.get_coupon(
            db=db,
            coupon_id=coupon_id,
            current_user=current_user,
        )

        update_data = coupon_data.model_dump(
            exclude_unset=True
        )

        old_data = {}

        for key in update_data:
            old_value = getattr(coupon, key)

            if isinstance(old_value, Decimal):
                old_value = str(old_value)

            elif isinstance(old_value, datetime):
                old_value = old_value.isoformat()

            old_data[key] = old_value

        for key, value in update_data.items():
            setattr(coupon, key, value)

        coupon.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(coupon)

        new_data = {}

        for key in update_data:
            new_value = getattr(coupon, key)

            if isinstance(new_value, Decimal):
                new_value = str(new_value)

            elif isinstance(new_value, datetime):
                new_value = new_value.isoformat()

            new_data[key] = new_value

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=coupon.organization_id,
                action="coupon_updated",
                entity_type="coupon",
                entity_id=coupon.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "code": coupon.code,
                    "old_data": old_data,
                    "new_data": new_data,
                },
            ),
        )

        return coupon

    def delete_coupon(
        self,
        db: Session,
        coupon_id: int,
        current_user: User,
        request: Request,
    ):
        coupon = self.get_coupon(
            db=db,
            coupon_id=coupon_id,
            current_user=current_user,
        )

        organization_id = coupon.organization_id
        deleted_coupon_id = coupon.id
        coupon_code = coupon.code

        db.delete(coupon)
        db.commit()

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="coupon_deleted",
                entity_type="coupon",
                entity_id=deleted_coupon_id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "code": coupon_code,
                },
            ),
        )

        return {
            "message": "Coupon deleted successfully"
        }

    def validate_coupon(
        self,
        db: Session,
        organization_id: int,
        code: str,
        amount: Decimal,
        current_user: User,
        request: Request,
    ):
        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        coupon = (
            db.query(Coupon)
            .filter(
                Coupon.organization_id == organization_id,
                Coupon.code == code.strip().upper(),
            )
            .first()
        )

        if not coupon:
            raise HTTPException(
                status_code=404,
                detail="Coupon not found",
            )

        if not coupon.is_active:
            raise HTTPException(
                status_code=400,
                detail="Coupon is inactive",
            )

        if (
            coupon.expires_at
            and coupon.expires_at < datetime.utcnow()
        ):
            raise HTTPException(
                status_code=400,
                detail="Coupon expired",
            )

        if coupon.used_count >= coupon.usage_limit:
            raise HTTPException(
                status_code=400,
                detail="Coupon usage limit exceeded",
            )

        if amount < coupon.minimum_amount:
            raise HTTPException(
                status_code=400,
                detail="Minimum amount not reached",
            )

        if coupon.discount_type == "percentage":
            discount = (
                amount * coupon.discount_value
            ) / Decimal("100")

            if (
                coupon.max_discount is not None
                and discount > coupon.max_discount
            ):
                discount = coupon.max_discount

        else:
            discount = coupon.discount_value

        if discount > amount:
            discount = amount

        final_amount = amount - discount

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="coupon_validated",
                entity_type="coupon",
                entity_id=coupon.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "code": coupon.code,
                    "original_amount": str(amount),
                    "discount_amount": str(discount),
                    "final_amount": str(final_amount),
                },
            ),
        )

        return {
            "valid": True,
            "code": coupon.code,
            "discount_amount": discount,
            "final_amount": final_amount,
            "message": "Coupon applied successfully",
        }