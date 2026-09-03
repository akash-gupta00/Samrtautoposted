from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.subscription import Subscription

from app.schemas.audit_log import AuditLogCreate
from app.schemas.payment import PaymentCreate

from app.services.audit_log_service import AuditLogService


class PaymentService:

    def get_subscription(
        self,
        db: Session,
        subscription_id: int,
    ):
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.id == subscription_id
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found",
            )

        return subscription

    def create_payment(
        self,
        db: Session,
        payment_data: PaymentCreate,
        current_user,
        request: Request,
    ):
        subscription = self.get_subscription(
            db=db,
            subscription_id=payment_data.subscription_id,
        )

        if subscription.organization.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this subscription",
            )

        if payment_data.transaction_id:
            existing_payment = (
                db.query(Payment)
                .filter(
                    Payment.transaction_id
                    == payment_data.transaction_id
                )
                .first()
            )

            if existing_payment:
                raise HTTPException(
                    status_code=400,
                    detail="Transaction already exists",
                )

        paid_at = None

        success_statuses = [
            "success",
            "paid",
            "captured",
        ]

        if payment_data.status in success_statuses:
            paid_at = datetime.now(timezone.utc)

        payment = Payment(
            subscription_id=payment_data.subscription_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            payment_gateway=payment_data.payment_gateway,
            transaction_id=payment_data.transaction_id,
            status=payment_data.status,
            paid_at=paid_at,
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        action = "payment_created"

        if payment.status in success_statuses:
            action = "payment_success"

        elif payment.status == "failed":
            action = "payment_failed"

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=subscription.organization_id,
                action=action,
                entity_type="payment",
                entity_id=payment.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "subscription_id": payment.subscription_id,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "payment_gateway": payment.payment_gateway,
                    "transaction_id": payment.transaction_id,
                    "status": payment.status,
                    "paid_at": (
                        payment.paid_at.isoformat()
                        if payment.paid_at
                        else None
                    ),
                },
            ),
        )

        return payment

    def list_payments(
        self,
        db: Session,
        organization_id: int,
        current_user,
    ):
        payments = (
            db.query(Payment)
            .join(
                Subscription,
                Payment.subscription_id == Subscription.id,
            )
            .filter(
                Subscription.organization_id == organization_id,
            )
            .order_by(
                Payment.created_at.desc()
            )
            .all()
        )

        if not payments:
            return []

        if (
            payments[0]
            .subscription
            .organization
            .owner_id
            != current_user.id
        ):
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

        return payments

    def get_payment(
        self,
        db: Session,
        payment_id: int,
        current_user,
    ):
        payment = (
            db.query(Payment)
            .filter(
                Payment.id == payment_id
            )
            .first()
        )

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        if (
            payment.subscription.organization.owner_id
            != current_user.id
        ):
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

        return payment