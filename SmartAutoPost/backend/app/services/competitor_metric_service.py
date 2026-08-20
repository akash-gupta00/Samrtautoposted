from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.competitor import Competitor
from app.models.competitor_metric import CompetitorMetric
from app.models.organization import Organization
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate
from app.schemas.competitor_metric import (
    CompetitorMetricCreate,
    CompetitorMetricUpdate,
)

from app.services.audit_log_service import AuditLogService


class CompetitorMetricService:

    def check_organization_access(
        self,
        db: Session,
        organization_id: int,
        current_user: User,
    ):
        """
        Check karega ki current user organization ka owner hai ya nahi.
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

    def get_competitor_with_access(
        self,
        db: Session,
        competitor_id: int,
        current_user: User,
    ):
        """
        Competitor find karega aur organization access check karega.
        """

        competitor = (
            db.query(Competitor)
            .filter(
                Competitor.id == competitor_id,
            )
            .first()
        )

        if not competitor:
            raise HTTPException(
                status_code=404,
                detail="Competitor not found",
            )

        self.check_organization_access(
            db=db,
            organization_id=competitor.organization_id,
            current_user=current_user,
        )

        return competitor

    def create_metric(
        self,
        db: Session,
        metric_data: CompetitorMetricCreate,
        current_user: User,
        request: Request,
    ):
        """
        Competitor ke liye naya metric record create karega.
        """

        competitor = self.get_competitor_with_access(
            db=db,
            competitor_id=metric_data.competitor_id,
            current_user=current_user,
        )

        metric = CompetitorMetric(
            competitor_id=metric_data.competitor_id,
            followers=metric_data.followers,
            following=metric_data.following,
            total_posts=metric_data.total_posts,
            average_likes=metric_data.average_likes,
            average_comments=metric_data.average_comments,
            average_shares=metric_data.average_shares,
            engagement_rate=metric_data.engagement_rate,
        )

        db.add(metric)
        db.commit()
        db.refresh(metric)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=competitor.organization_id,
                action="competitor_metric_created",
                entity_type="competitor_metric",
                entity_id=metric.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "competitor_id": competitor.id,
                    "competitor_name": competitor.name,
                    "platform": competitor.platform,
                    "followers": metric.followers,
                    "following": metric.following,
                    "total_posts": metric.total_posts,
                    "average_likes": metric.average_likes,
                    "average_comments": metric.average_comments,
                    "average_shares": metric.average_shares,
                    "engagement_rate": metric.engagement_rate,
                    "recorded_at": (
                        metric.recorded_at.isoformat()
                        if metric.recorded_at
                        else None
                    ),
                },
            ),
        )

        return metric

    def list_metrics(
        self,
        db: Session,
        competitor_id: int,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Competitor ke saare metric records return karega.
        """

        self.get_competitor_with_access(
            db=db,
            competitor_id=competitor_id,
            current_user=current_user,
        )

        metrics = (
            db.query(CompetitorMetric)
            .filter(
                CompetitorMetric.competitor_id
                == competitor_id
            )
            .order_by(
                CompetitorMetric.recorded_at.desc()
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return metrics

    def get_metric(
        self,
        db: Session,
        metric_id: int,
        competitor_id: int,
        current_user: User,
    ):
        """
        Ek particular competitor metric return karega.
        """

        self.get_competitor_with_access(
            db=db,
            competitor_id=competitor_id,
            current_user=current_user,
        )

        metric = (
            db.query(CompetitorMetric)
            .filter(
                CompetitorMetric.id == metric_id,
                CompetitorMetric.competitor_id
                == competitor_id,
            )
            .first()
        )

        if not metric:
            raise HTTPException(
                status_code=404,
                detail="Competitor metric not found",
            )

        return metric
    
    def update_metric(
        self,
        db: Session,
        metric_id: int,
        competitor_id: int,
        metric_data: CompetitorMetricUpdate,
        current_user: User,
        request: Request,
    ):
        """
        Existing competitor metric update karega.
        """

        metric = self.get_metric(
            db=db,
            metric_id=metric_id,
            competitor_id=competitor_id,
            current_user=current_user,
        )

        competitor = self.get_competitor_with_access(
            db=db,
            competitor_id=competitor_id,
            current_user=current_user,
        )

        update_data = metric_data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided",
            )

        old_data = {
            "followers": metric.followers,
            "following": metric.following,
            "total_posts": metric.total_posts,
            "average_likes": metric.average_likes,
            "average_comments": metric.average_comments,
            "average_shares": metric.average_shares,
            "engagement_rate": metric.engagement_rate,
        }

        for field, value in update_data.items():
            setattr(metric, field, value)

        db.commit()
        db.refresh(metric)

        changed_fields = {}

        for field in update_data:
            changed_fields[field] = {
                "old": old_data.get(field),
                "new": getattr(metric, field),
            }

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=competitor.organization_id,
                action="competitor_metric_updated",
                entity_type="competitor_metric",
                entity_id=metric.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "competitor_name": competitor.name,
                    "changed_fields": changed_fields,
                },
            ),
        )

        return metric

    def delete_metric(
        self,
        db: Session,
        metric_id: int,
        competitor_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Competitor metric delete karega.
        """

        metric = self.get_metric(
            db=db,
            metric_id=metric_id,
            competitor_id=competitor_id,
            current_user=current_user,
        )

        competitor = self.get_competitor_with_access(
            db=db,
            competitor_id=competitor_id,
            current_user=current_user,
        )

        deleted_metric = {
            "followers": metric.followers,
            "following": metric.following,
            "total_posts": metric.total_posts,
            "average_likes": metric.average_likes,
            "average_comments": metric.average_comments,
            "average_shares": metric.average_shares,
            "engagement_rate": metric.engagement_rate,
        }

        metric_id_value = metric.id

        db.delete(metric)
        db.commit()

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=competitor.organization_id,
                action="competitor_metric_deleted",
                entity_type="competitor_metric",
                entity_id=metric_id_value,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details=deleted_metric,
            ),
        )

        return {
            "message": "Competitor metric deleted successfully",
            "metric_id": metric_id_value,
        }
    
