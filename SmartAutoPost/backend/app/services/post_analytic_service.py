from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.post import Post
from app.models.post_analytic import PostAnalytic
from app.models.user import User

from app.schemas.audit_log import AuditLogCreate
from app.schemas.post_analytic import (
    PostAnalyticCreate,
    PostAnalyticUpdate,
)

from app.services.audit_log_service import AuditLogService


class PostAnalyticService:

    def check_post_access(
        self,
        db: Session,
        post_id: int,
        current_user: User,
    ):
        """
        Check karega ki post current user ki organization ka hai ya nahi.
        """

        post = (
            db.query(Post)
            .join(
                Organization,
                Post.organization_id == Organization.id,
            )
            .filter(
                Post.id == post_id,
                Organization.owner_id == current_user.id,
            )
            .first()
        )

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Post not found or access denied",
            )

        return post

    def create_analytic(
        self,
        db: Session,
        analytic_data: PostAnalyticCreate,
        current_user: User,
        request: Request,
    ):
        """
        New analytic record create karega.
        """

        post = self.check_post_access(
            db=db,
            post_id=analytic_data.post_id,
            current_user=current_user,
        )

        analytic = PostAnalytic(
            post_id=analytic_data.post_id,
            platform=analytic_data.platform,
            platform_post_id=analytic_data.platform_post_id,
            impressions=analytic_data.impressions,
            reach=analytic_data.reach,
            likes=analytic_data.likes,
            comments=analytic_data.comments,
            shares=analytic_data.shares,
            clicks=analytic_data.clicks,
            saves=analytic_data.saves,
            engagement_rate=analytic_data.engagement_rate,
        )

        db.add(analytic)
        db.commit()
        db.refresh(analytic)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=post.organization_id,
                action="post_analytic_created",
                entity_type="post_analytic",
                entity_id=analytic.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "post_id": post.id,
                    "platform": analytic.platform,
                    "impressions": analytic.impressions,
                    "reach": analytic.reach,
                    "likes": analytic.likes,
                    "comments": analytic.comments,
                    "shares": analytic.shares,
                    "clicks": analytic.clicks,
                    "saves": analytic.saves,
                    "engagement_rate": analytic.engagement_rate,
                },
            ),
        )

        return analytic

    def list_analytics(
        self,
        db: Session,
        post_id: int,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ):
        """
        Post ke saare analytics return karega.
        """

        self.check_post_access(
            db=db,
            post_id=post_id,
            current_user=current_user,
        )

        return (
            db.query(PostAnalytic)
            .filter(
                PostAnalytic.post_id == post_id,
            )
            .order_by(
                PostAnalytic.recorded_at.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_analytic(
        self,
        db: Session,
        analytic_id: int,
        post_id: int,
        current_user: User,
    ):
        """
        Single analytic record return karega.
        """

        self.check_post_access(
            db=db,
            post_id=post_id,
            current_user=current_user,
        )

        analytic = (
            db.query(PostAnalytic)
            .filter(
                PostAnalytic.id == analytic_id,
                PostAnalytic.post_id == post_id,
            )
            .first()
        )

        if not analytic:
            raise HTTPException(
                status_code=404,
                detail="Post analytic not found",
            )

        return analytic
    
    def update_analytic(
        self,
        db: Session,
        analytic_id: int,
        post_id: int,
        analytic_data: PostAnalyticUpdate,
        current_user: User,
        request: Request,
    ):
        """
        Existing post analytic update karega.
        """

        analytic = self.get_analytic(
            db=db,
            analytic_id=analytic_id,
            post_id=post_id,
            current_user=current_user,
        )

        post = self.check_post_access(
            db=db,
            post_id=post_id,
            current_user=current_user,
        )

        update_data = analytic_data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No update data provided",
            )

        old_data = {
            "platform": analytic.platform,
            "platform_post_id": analytic.platform_post_id,
            "impressions": analytic.impressions,
            "reach": analytic.reach,
            "likes": analytic.likes,
            "comments": analytic.comments,
            "shares": analytic.shares,
            "clicks": analytic.clicks,
            "saves": analytic.saves,
            "engagement_rate": analytic.engagement_rate,
        }

        for field, value in update_data.items():
            setattr(analytic, field, value)

        db.commit()
        db.refresh(analytic)

        changed_fields = {}

        for field in update_data:
            changed_fields[field] = {
                "old": old_data.get(field),
                "new": getattr(analytic, field),
            }

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=post.organization_id,
                action="post_analytic_updated",
                entity_type="post_analytic",
                entity_id=analytic.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details={
                    "post_id": post.id,
                    "changed_fields": changed_fields,
                },
            ),
        )

        return analytic

    def delete_analytic(
        self,
        db: Session,
        analytic_id: int,
        post_id: int,
        current_user: User,
        request: Request,
    ):
        """
        Post analytic delete karega.
        """

        analytic = self.get_analytic(
            db=db,
            analytic_id=analytic_id,
            post_id=post_id,
            current_user=current_user,
        )

        post = self.check_post_access(
            db=db,
            post_id=post_id,
            current_user=current_user,
        )

        deleted_data = {
            "platform": analytic.platform,
            "platform_post_id": analytic.platform_post_id,
            "impressions": analytic.impressions,
            "reach": analytic.reach,
            "likes": analytic.likes,
            "comments": analytic.comments,
            "shares": analytic.shares,
            "clicks": analytic.clicks,
            "saves": analytic.saves,
            "engagement_rate": analytic.engagement_rate,
        }

        analytic_id_value = analytic.id

        db.delete(analytic)
        db.commit()

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=post.organization_id,
                action="post_analytic_deleted",
                entity_type="post_analytic",
                entity_id=analytic_id_value,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "user-agent"
                ),
                details=deleted_data,
            ),
        )

        return {
            "message": "Post analytic deleted successfully",
            "analytic_id": analytic_id_value,
        }