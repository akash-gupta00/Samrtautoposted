from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.organization import Organization
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService


class InvoiceService:

    def check_organization_access(
        self,
        db: Session,
        organization_id: int,
        current_user,
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
                status_code=403,
                detail="Organization not found or access denied",
            )

        return organization

    def generate_invoice_number(self):
        now = datetime.now(timezone.utc)

        return (
            f"INV-"
            f"{now.strftime('%Y%m%d')}-"
            f"{uuid4().hex[:8].upper()}"
        )

    def create_invoice_from_payment(
        self,
        db: Session,
        payment_id: int,
        current_user,
        request: Request,
    ):
        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id)
            .first()
        )

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        successful_statuses = [
            "success",
            "paid",
            "captured",
        ]

        if payment.status not in successful_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invoice can only be created "
                    "for successful payment"
                ),
            )

        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.id == payment.subscription_id
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found",
            )

        self.check_organization_access(
            db=db,
            organization_id=subscription.organization_id,
            current_user=current_user,
        )

        # Ek payment ka sirf ek invoice banega.
        existing_invoice = (
            db.query(Invoice)
            .filter(
                Invoice.payment_id == payment.id
            )
            .first()
        )

        if existing_invoice:
            return existing_invoice

        plan = (
            db.query(Plan)
            .filter(
                Plan.id == subscription.plan_id
            )
            .first()
        )

        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Plan not found",
            )

        amount = Decimal(str(payment.amount))
        tax_amount = Decimal("0.00")
        total_amount = amount + tax_amount

        invoice = Invoice(
            invoice_number=self.generate_invoice_number(),
            organization_id=subscription.organization_id,
            subscription_id=subscription.id,
            payment_id=payment.id,
            plan_name=plan.name,
            amount=amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency=payment.currency,
            status="paid",
            issued_at=datetime.now(timezone.utc),
        )

        try:
            db.add(invoice)
            db.commit()
            db.refresh(invoice)

            AuditLogService.create_log(
                db=db,
                audit_data=AuditLogCreate(
                    user_id=current_user.id,
                    organization_id=invoice.organization_id,
                    action="invoice_created",
                    entity_type="invoice",
                    entity_id=invoice.id,
                    ip_address=(
                        request.client.host
                        if request.client
                        else None
                    ),
                    user_agent=request.headers.get(
                        "user-agent"
                    ),
                    details={
                        "invoice_number": invoice.invoice_number,
                        "payment_id": invoice.payment_id,
                        "subscription_id": invoice.subscription_id,
                        "plan_name": invoice.plan_name,
                        "amount": str(invoice.amount),
                        "tax_amount": str(invoice.tax_amount),
                        "total_amount": str(invoice.total_amount),
                        "currency": invoice.currency,
                        "status": invoice.status,
                        "issued_at": (
                            invoice.issued_at.isoformat()
                            if invoice.issued_at
                            else None
                        ),
                    },
                ),
            )

            return invoice

        except Exception:
            db.rollback()
            raise

    def list_invoices(
        self,
        db: Session,
        organization_id: int,
        current_user,
    ):
        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        return (
            db.query(Invoice)
            .filter(
                Invoice.organization_id == organization_id
            )
            .order_by(
                Invoice.created_at.desc()
            )
            .all()
        )

    def get_invoice(
        self,
        db: Session,
        invoice_id: int,
        current_user,
    ):
        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id == invoice_id
            )
            .first()
        )

        if not invoice:
            raise HTTPException(
                status_code=404,
                detail="Invoice not found",
            )

        self.check_organization_access(
            db=db,
            organization_id=invoice.organization_id,
            current_user=current_user,
        )

        return invoice