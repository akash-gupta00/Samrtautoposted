from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.plan import Plan
from app.models.subscription import Subscription

from app.schemas.audit_log import AuditLogCreate
from app.schemas.subscription import SubscriptionCreate

from app.services.audit_log_service import AuditLogService


class SubscriptionService:

    def check_organization_access(
        self,
        db: Session,
        organization_id: int,
        current_user,
    ):
        """
        Check karega ki logged-in user organization ka owner hai ya nahi.
        """

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

    def get_active_plan(
        self,
        db: Session,
        plan_id: int,
    ):
        """
        Active subscription plan return karega.
        """

        plan = (
            db.query(Plan)
            .filter(
                Plan.id == plan_id,
                Plan.is_active.is_(True),
            )
            .first()
        )

        if not plan:
            raise HTTPException(
                status_code=404,
                detail="Active plan not found",
            )

        return plan

    def create_subscription(
        self,
        db: Session,
        subscription_data: SubscriptionCreate,
        current_user,
        request: Request,
    ):
        """
        Organization ke liye nayi subscription create karega.
        """

        self.check_organization_access(
            db=db,
            organization_id=subscription_data.organization_id,
            current_user=current_user,
        )

        plan = self.get_active_plan(
            db=db,
            plan_id=subscription_data.plan_id,
        )

        existing_subscription = (
            db.query(Subscription)
            .filter(
                Subscription.organization_id
                == subscription_data.organization_id,
                Subscription.status == "active",
            )
            .first()
        )

        if existing_subscription:
            raise HTTPException(
                status_code=400,
                detail="Organization already has an active subscription",
            )

        now = datetime.now(timezone.utc)

        if plan.billing_cycle == "yearly":
            end_date = now + timedelta(days=365)
        else:
            end_date = now + timedelta(days=30)

        subscription = Subscription(
            organization_id=subscription_data.organization_id,
            plan_id=subscription_data.plan_id,
            status="active",
            start_date=now,
            end_date=end_date,
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # Subscription create hone ka audit log.
        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=subscription.organization_id,
                action="subscription_created",
                entity_type="subscription",
                entity_id=subscription.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "plan_id": subscription.plan_id,
                    "plan_name": getattr(plan, "name", None),
                    "billing_cycle": plan.billing_cycle,
                    "status": subscription.status,
                    "start_date": subscription.start_date.isoformat(),
                    "end_date": (
                        subscription.end_date.isoformat()
                        if subscription.end_date
                        else None
                    ),
                },
            ),
        )

        return subscription

    def get_current_subscription(
        self,
        db: Session,
        organization_id: int,
        current_user,
    ):
        """
        Organization ki active subscription return karega.
        """

        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.organization_id == organization_id,
                Subscription.status == "active",
            )
            .order_by(
                Subscription.created_at.desc(),
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Active subscription not found",
            )

        return subscription

    def cancel_subscription(
        self,
        db: Session,
        organization_id: int,
        current_user,
        request: Request,
    ):
        """
        Organization ki current active subscription cancel karega.
        """

        subscription = self.get_current_subscription(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        old_status = subscription.status

        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(subscription)

        # Subscription cancel hone ka audit log.
        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=subscription.organization_id,
                action="subscription_cancelled",
                entity_type="subscription",
                entity_id=subscription.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "plan_id": subscription.plan_id,
                    "old_status": old_status,
                    "new_status": subscription.status,
                    "cancelled_at": (
                        subscription.cancelled_at.isoformat()
                        if subscription.cancelled_at
                        else None
                    ),
                },
            ),
        )

        return subscription

    def list_subscriptions(
        self,
        db: Session,
        organization_id: int,
        current_user,
    ):
        """
        Organization ki saari subscriptions return karega.
        """

        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        return (
            db.query(Subscription)
            .filter(
                Subscription.organization_id == organization_id,
            )
            .order_by(
                Subscription.created_at.desc(),
            )
            .all()
        )