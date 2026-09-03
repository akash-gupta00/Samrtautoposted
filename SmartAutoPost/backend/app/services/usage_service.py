from calendar import monthrange
from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.usage_log import UsageLog
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate

from app.services.audit_log_service import AuditLogService


class UsageService:

    POST_USAGE = "post"
    AI_USAGE = "ai_generation"
    SOCIAL_ACCOUNT_USAGE = "social_account"

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
                status_code=403,
                detail="Organization not found or access denied",
            )

        return organization

    def get_month_period(self):
        now = datetime.now(timezone.utc)

        period_start = datetime(
            year=now.year,
            month=now.month,
            day=1,
            tzinfo=timezone.utc,
        )

        last_day = monthrange(
            now.year,
            now.month,
        )[1]

        period_end = datetime(
            year=now.year,
            month=now.month,
            day=last_day,
            hour=23,
            minute=59,
            second=59,
            tzinfo=timezone.utc,
        )

        return period_start, period_end

    def get_organization_plan(
        self,
        db: Session,
        organization_id: int,
    ):
        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.organization_id == organization_id,
                Subscription.status == "active",
            )
            .order_by(
                Subscription.created_at.desc()
            )
            .first()
        )

        if subscription:
            plan = (
                db.query(Plan)
                .filter(
                    Plan.id == subscription.plan_id,
                    Plan.is_active.is_(True),
                )
                .first()
            )

            if plan:
                return plan

        free_plan = (
            db.query(Plan)
            .filter(
                Plan.name == "Free",
                Plan.is_active.is_(True),
            )
            .first()
        )

        if not free_plan:
            raise HTTPException(
                status_code=404,
                detail="No active subscription or Free plan found",
            )

        return free_plan

    def get_usage(
        self,
        db: Session,
        organization_id: int,
        usage_type: str,
    ):
        period_start, period_end = self.get_month_period()

        usage = (
            db.query(UsageLog)
            .filter(
                UsageLog.organization_id == organization_id,
                UsageLog.usage_type == usage_type,
                UsageLog.period_start == period_start,
                UsageLog.period_end == period_end,
            )
            .first()
        )

        if usage:
            return usage

        usage = UsageLog(
            organization_id=organization_id,
            usage_type=usage_type,
            usage_count=0,
            period_start=period_start,
            period_end=period_end,
        )

        db.add(usage)
        db.commit()
        db.refresh(usage)

        return usage

    def get_limit(
        self,
        plan: Plan,
        usage_type: str,
    ):
        limit_mapping = {
            self.POST_USAGE: plan.max_posts_per_month,
            self.AI_USAGE: plan.max_ai_generations,
            self.SOCIAL_ACCOUNT_USAGE: plan.max_social_accounts,
        }

        limit = limit_mapping.get(usage_type)

        if limit is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid usage type: {usage_type}",
            )

        return limit

    def check_limit(
        self,
        db: Session,
        organization_id: int,
        usage_type: str,
    ):
        plan = self.get_organization_plan(
            db=db,
            organization_id=organization_id,
        )

        usage = self.get_usage(
            db=db,
            organization_id=organization_id,
            usage_type=usage_type,
        )

        allowed_limit = self.get_limit(
            plan=plan,
            usage_type=usage_type,
        )

        if usage.usage_count >= allowed_limit:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"{usage_type} limit exceeded for "
                    f"{plan.name} plan. "
                    "Please upgrade your subscription."
                ),
            )

        return {
            "allowed": True,
            "plan": plan.name,
            "usage_type": usage_type,
            "used": usage.usage_count,
            "limit": allowed_limit,
            "remaining": (
                allowed_limit - usage.usage_count
            ),
        }

    def increment_usage(
        self,
        db: Session,
        organization_id: int,
        usage_type: str,
        increment_by: int,
        current_user: User,
        request: Request,
    ):
        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        if increment_by <= 0:
            raise HTTPException(
                status_code=400,
                detail="increment_by must be greater than zero",
            )

        self.check_limit(
            db=db,
            organization_id=organization_id,
            usage_type=usage_type,
        )

        usage = self.get_usage(
            db=db,
            organization_id=organization_id,
            usage_type=usage_type,
        )

        plan = self.get_organization_plan(
            db=db,
            organization_id=organization_id,
        )

        allowed_limit = self.get_limit(
            plan=plan,
            usage_type=usage_type,
        )

        old_usage_count = usage.usage_count
        new_usage_count = old_usage_count + increment_by

        if new_usage_count > allowed_limit:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"{usage_type} limit exceeded for "
                    f"{plan.name} plan."
                ),
            )

        usage.usage_count = new_usage_count

        db.commit()
        db.refresh(usage)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="usage_updated",
                entity_type="usage",
                entity_id=usage.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "usage_type": usage.usage_type,
                    "plan_name": plan.name,
                    "increment_by": increment_by,
                    "old_usage_count": old_usage_count,
                    "new_usage_count": usage.usage_count,
                    "allowed_limit": allowed_limit,
                    "remaining": (
                        allowed_limit
                        - usage.usage_count
                    ),
                    "period_start": (
                        usage.period_start.isoformat()
                        if usage.period_start
                        else None
                    ),
                    "period_end": (
                        usage.period_end.isoformat()
                        if usage.period_end
                        else None
                    ),
                },
            ),
        )

        return usage

    def get_remaining_usage(
        self,
        db: Session,
        organization_id: int,
        usage_type: str,
        current_user: User,
    ):
        self.check_organization_access(
            db=db,
            organization_id=organization_id,
            current_user=current_user,
        )

        plan = self.get_organization_plan(
            db=db,
            organization_id=organization_id,
        )

        usage = self.get_usage(
            db=db,
            organization_id=organization_id,
            usage_type=usage_type,
        )

        allowed_limit = self.get_limit(
            plan=plan,
            usage_type=usage_type,
        )

        remaining = max(
            allowed_limit - usage.usage_count,
            0,
        )

        return {
            "plan": plan.name,
            "usage_type": usage_type,
            "used": usage.usage_count,
            "limit": allowed_limit,
            "remaining": remaining,
            "period_start": usage.period_start,
            "period_end": usage.period_end,
        }

    def get_usage_summary(
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

        plan = self.get_organization_plan(
            db=db,
            organization_id=organization_id,
        )

        post_usage = self.get_remaining_usage(
            db=db,
            organization_id=organization_id,
            usage_type=self.POST_USAGE,
            current_user=current_user,
        )

        ai_usage = self.get_remaining_usage(
            db=db,
            organization_id=organization_id,
            usage_type=self.AI_USAGE,
            current_user=current_user,
        )

        social_usage = self.get_remaining_usage(
            db=db,
            organization_id=organization_id,
            usage_type=self.SOCIAL_ACCOUNT_USAGE,
            current_user=current_user,
        )

        return {
            "organization_id": organization_id,
            "plan_id": plan.id,
            "plan_name": plan.name,
            "posts": post_usage,
            "ai_generations": ai_usage,
            "social_accounts": social_usage,
        }