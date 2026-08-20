from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.enums import PostStatus
from app.dependencies.permission import check_user_permission
from app.models.media import Media
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.post import Post
from app.models.social_account import SocialAccount
from app.repositories.post_repository import PostRepository
from app.schemas.audit_log import AuditLogCreate
from app.schemas.post import AttachMediaRequest
from app.services.audit_log_service import AuditLogService
from app.services.publisher_service import PublisherService


class PostService:

    def __init__(self):
        self.repository = PostRepository()
        self.publisher = PublisherService()

    def check_organization_access(
        self,
        db: Session,
        organization_id: int,
        current_user,
    ):
        organization = (
            db.query(Organization)
            .outerjoin(
                OrganizationMember,
                OrganizationMember.organization_id == Organization.id,
            )
            .filter(
                Organization.id == organization_id,
                (
                    (Organization.owner_id == current_user.id)
                    | (OrganizationMember.user_id == current_user.id)
                ),
            )
            .first()
        )

        if not organization:
            raise HTTPException(
                status_code=403,
                detail="Organization not found or access denied",
            )

        return organization

    def get_post_record(
        self,
        db: Session,
        post_id: int,
    ):
        post = (
            db.query(Post)
            .filter(Post.id == post_id)
            .first()
        )

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Post not found",
            )

        return post

    def create_post_audit_log(
        self,
        db: Session,
        request: Request | None,
        current_user,
        organization_id: int,
        action: str,
        post_id: int | None = None,
        details: dict | None = None,
    ):
        try:
            AuditLogService.create_log(
                db=db,
                audit_data=AuditLogCreate(
                    user_id=current_user.id if current_user else 1,
                    organization_id=organization_id,
                    action=action,
                    entity_type="post",
                    entity_id=post_id,
                    ip_address=(
                        request.client.host
                        if request and request.client
                        else None
                    ),
                    user_agent=request.headers.get("user-agent") if request else None,
                    details=details,
                ),
            )
        except Exception as error:
            db.rollback()
            print(f"Post audit log error: {error}")

    def get_media_records(
        self,
        db: Session,
        media_ids: list[int],
        organization_id: int,
    ):
        if not media_ids:
            return []

        unique_media_ids = list(set(media_ids))

        media_records = (
            db.query(Media)
            .filter(
                Media.id.in_(unique_media_ids),
                Media.organization_id == organization_id,
            )
            .all()
        )

        if len(media_records) != len(unique_media_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more media files were not found in this organization",
            )

        return media_records

    # =========================================================
    # CREATE POST
    # =========================================================
    def create_post(
        self,
        db: Session,
        post_data,
        current_user,
        request: Request | None = None,
    ):
        self.check_organization_access(
            db=db,
            organization_id=post_data.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=post_data.organization_id,
            permission_name="posts.create",
        )

        post_status = PostStatus.DRAFT.value
        if post_data.scheduled_at is not None:
            post_status = PostStatus.SCHEDULED.value

        post = Post(
            organization_id=post_data.organization_id,
            social_account_id=post_data.social_account_id,
            title=post_data.title,
            caption=post_data.caption,
            scheduled_at=post_data.scheduled_at,
            status=post_status,
        )

        if post_data.media_ids:
            post.media = self.get_media_records(
                db=db,
                media_ids=post_data.media_ids,
                organization_id=post_data.organization_id,
            )

        db.add(post)
        db.commit()
        db.refresh(post)

        self.create_post_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=post.organization_id,
            action="post_created",
            post_id=post.id,
            details={
                "title": post.title,
                "status": post.status,
                "social_account_id": post.social_account_id,
                "media_ids": [media.id for media in post.media],
            },
        )

        return post

    # =========================================================
    # PUBLISH POST NOW (Direct to Instagram)
    # =========================================================
    def publish_post(
        self,
        db: Session,
        post_id: int,
        current_user,
        request: Request | None = None,
    ):
        post = self.get_post_record(db=db, post_id=post_id)

        self.check_organization_access(
            db=db,
            organization_id=post.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=post.organization_id,
            permission_name="publish.post",
        )

        if post.status == PostStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=400,
                detail="Post is already published",
            )

        base_url = (
            str(request.base_url).rstrip("/")
            if request
            else "https://samrtautoposted.onrender.com"
        )

        result = self.publisher.publish_post(
            db=db,
            post=post,
            base_url=base_url,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Publishing failed"),
            )

        post.status = PostStatus.PUBLISHED.value
        db.commit()
        db.refresh(post)

        self.create_post_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=post.organization_id,
            action="post_published",
            post_id=post.id,
            details={
                "platform": "instagram",
                "instagram_post_id": result.get("instagram_post_id"),
            },
        )

        return post

    # =========================================================
    # LIST POSTS
    # =========================================================
    def list_posts(
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

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=organization_id,
            permission_name="posts.view",
        )

        return (
            db.query(Post)
            .filter(Post.organization_id == organization_id)
            .order_by(Post.created_at.desc())
            .all()
        )

    # =========================================================
    # SINGLE POST DETAIL
    # =========================================================
    def get_post_detail(
        self,
        db: Session,
        post_id: int,
        current_user,
    ):
        post = self.get_post_record(db=db, post_id=post_id)

        self.check_organization_access(
            db=db,
            organization_id=post.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=post.organization_id,
            permission_name="posts.view",
        )

        return post

    # =========================================================
    # UPDATE POST
    # =========================================================
    def update_post(
        self,
        db: Session,
        post_id: int,
        post_data,
        current_user,
        request: Request | None = None,
    ):
        post = self.get_post_record(db=db, post_id=post_id)

        self.check_organization_access(
            db=db,
            organization_id=post.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=post.organization_id,
            permission_name="posts.update",
        )

        update_data = post_data.model_dump(exclude_unset=True)
        media_ids = update_data.pop("media_ids", None)

        for field, value in update_data.items():
            setattr(post, field, value)

        if "scheduled_at" in update_data:
            if post.scheduled_at is not None:
                post.status = PostStatus.SCHEDULED.value
            elif post.status == PostStatus.SCHEDULED.value:
                post.status = PostStatus.DRAFT.value

        if media_ids is not None:
            post.media = self.get_media_records(
                db=db,
                media_ids=media_ids,
                organization_id=post.organization_id,
            )

        db.commit()
        db.refresh(post)

        self.create_post_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=post.organization_id,
            action="post_updated",
            post_id=post.id,
            details={"title": post.title, "status": post.status},
        )

        return post

    # =========================================================
    # DELETE POST (With Foreign Key Cascade Cleanup)
    # =========================================================
    def delete_post(
        self,
        db: Session,
        post_id: int,
        current_user,
        request: Request | None = None,
    ):
        post = self.get_post_record(db=db, post_id=post_id)

        self.check_organization_access(
            db=db,
            organization_id=post.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=post.organization_id,
            permission_name="posts.delete",
        )

        organization_id = post.organization_id
        deleted_post_id = post.id

        try:
            self.create_post_audit_log(
                db=db,
                request=request,
                current_user=current_user,
                organization_id=organization_id,
                action="post_deleted",
                post_id=deleted_post_id,
                details={"title": post.title, "status": post.status},
            )

            # Foreign key tables se post_id ke records pehle delete karna
            db.execute(text("DELETE FROM publish_logs WHERE post_id = :pid"), {"pid": deleted_post_id})
            db.execute(text("DELETE FROM post_schedules WHERE post_id = :pid"), {"pid": deleted_post_id})
            db.execute(text("DELETE FROM post_analytics WHERE post_id = :pid"), {"pid": deleted_post_id})
            db.execute(text("DELETE FROM post_media WHERE post_id = :pid"), {"pid": deleted_post_id})
            db.commit()

            # Main post record delete karna
            db.execute(text("DELETE FROM posts WHERE id = :pid"), {"pid": deleted_post_id})
            db.commit()

            return {
                "success": True,
                "message": "Post deleted successfully",
            }
        except Exception as err:
            db.rollback()
            print(f"CRITICAL DELETE ERROR: {err}")
            raise HTTPException(
                status_code=500,
                detail=f"Delete failed: {str(err)}",
            )

    # =========================================================
    # SCHEDULE POST
    # =========================================================
    def schedule_post(
        self,
        db: Session,
        post_id: int,
        scheduled_at,
        current_user,
        request: Request | None = None,
    ):
        post = self.get_post_record(db=db, post_id=post_id)

        self.check_organization_access(
            db=db,
            organization_id=post.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=post.organization_id,
            permission_name="publish.post",
        )

        if post.status == PostStatus.PUBLISHED.value:
            raise HTTPException(
                status_code=400,
                detail="Published post cannot be scheduled",
            )

        post.scheduled_at = scheduled_at
        post.status = PostStatus.SCHEDULED.value
        db.commit()
        db.refresh(post)

        return post

    # =========================================================
    # ATTACH MEDIA TO POST
    # =========================================================
    def attach_media_to_post(
        self,
        db: Session,
        post_id: int,
        data: AttachMediaRequest,
        current_user,
        request: Request | None = None,
    ):
        post = self.get_post_record(db=db, post_id=post_id)

        self.check_organization_access(
            db=db,
            organization_id=post.organization_id,
            current_user=current_user,
        )

        check_user_permission(
            db=db,
            current_user=current_user,
            organization_id=post.organization_id,
            permission_name="posts.update",
        )

        media_records = self.get_media_records(
            db=db,
            media_ids=data.media_ids,
            organization_id=post.organization_id,
        )

        existing_media_ids = {media.id for media in post.media}
        for media in media_records:
            if media.id not in existing_media_ids:
                post.media.append(media)

        db.commit()
        db.refresh(post)
        return post