from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.models.organization import Organization
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.user import User
from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService


class RefundService:

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

    def create_refund(
        self,
        db: Session,
        payment_id: int,
        amount: Decimal,
        reason: str | None,
        current_user: User,
        request: Request,
    ):
        payment = (
            db.query(Payment)
            .options(
                joinedload(Payment.subscription)
            )
            .filter(
                Payment.id == payment_id
            )
            .first()
        )

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        if not payment.subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found for this payment",
            )

        organization_id = (
            payment.subscription.organization_id
        )

        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        successful_statuses = [
            "success",
            "successful",
            "paid",
            "captured",
        ]

        if (
            not payment.status
            or payment.status.lower()
            not in successful_statuses
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only successful payments can be refunded",
            )

        refund_amount_rows = (
            db.query(Refund.amount)
            .filter(
                Refund.payment_id == payment_id,
                Refund.status == "completed",
            )
            .all()
        )

        total_refunded = sum(
            (
                Decimal(str(row[0]))
                for row in refund_amount_rows
            ),
            Decimal("0.00"),
        )

        payment_amount = Decimal(
            str(payment.amount)
        )

        refund_amount = Decimal(
            str(amount)
        )

        remaining_amount = (
            payment_amount - total_refunded
        )

        if remaining_amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has already been fully refunded",
            )

        if refund_amount > remaining_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Refund amount cannot exceed "
                    f"remaining amount {remaining_amount}"
                ),
            )

        refund = Refund(
            payment_id=payment.id,
            organization_id=organization_id,
            amount=refund_amount,
            currency=payment.currency,
            reason=reason,
            status="completed",
            processed_at=datetime.utcnow(),
        )

        try:
            db.add(refund)
            db.commit()
            db.refresh(refund)

            AuditLogService.create_log(
                db=db,
                audit_data=AuditLogCreate(
                    user_id=current_user.id,
                    organization_id=refund.organization_id,
                    action="refund_completed",
                    entity_type="refund",
                    entity_id=refund.id,
                    ip_address=(
                        request.client.host
                        if request.client
                        else None
                    ),
                    user_agent=request.headers.get(
                        "user-agent"
                    ),
                    details={
                        "payment_id": refund.payment_id,
                        "refund_amount": str(
                            refund.amount
                        ),
                        "payment_amount": str(
                            payment_amount
                        ),
                        "previously_refunded": str(
                            total_refunded
                        ),
                        "remaining_after_refund": str(
                            remaining_amount
                            - refund_amount
                        ),
                        "currency": refund.currency,
                        "reason": refund.reason,
                        "status": refund.status,
                        "processed_at": (
                            refund.processed_at.isoformat()
                            if refund.processed_at
                            else None
                        ),
                    },
                ),
            )

            return refund

        except Exception:
            db.rollback()
            raise

    def list_refunds(
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
            db.query(Refund)
            .filter(
                Refund.organization_id
                == organization_id
            )
            .order_by(
                Refund.id.desc()
            )
            .all()
        )

    def get_refund(
        self,
        db: Session,
        refund_id: int,
        current_user: User,
    ):
        refund = (
            db.query(Refund)
            .filter(
                Refund.id == refund_id
            )
            .first()
        )

        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found",
            )

        self.check_organization_access(
            db=db,
            organization_id=refund.organization_id,
            current_user=current_user,
        )

        return refund