import httpx
from fastapi import HTTPException, Request
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


class PostService:

    def __init__(self):
        self.repository = PostRepository()

    # Organization owner ya member ka basic access check karega.
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

    # Internal helper: Sirf post record fetch karega.
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

    # Post actions ka audit log create karega.
    def create_post_audit_log(
        self,
        db: Session,
        request: Request,
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
                    user_id=current_user.id,
                    organization_id=organization_id,
                    action=action,
                    entity_type="post",
                    entity_id=post_id,
                    ip_address=(
                        request.client.host
                        if request.client
                        else None
                    ),
                    user_agent=request.headers.get("user-agent"),
                    details=details,
                ),
            )

        except Exception as error:
            db.rollback()
            print(f"Post audit log error: {error}")

    # Media IDs ke corresponding records return karega.
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
                detail=(
                    "One or more media files were not found "
                    "in this organization"
                ),
            )

        return media_records

    # =========================================================
    # CREATE POST
    # Required Permission: posts.create
    # =========================================================
    def create_post(
        self,
        db: Session,
        post_data,
        current_user,
        request: Request,
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
                "media_ids": [
                    media.id
                    for media in post.media
                ],
            },
        )

        if post.scheduled_at is not None:
            self.create_post_audit_log(
                db=db,
                request=request,
                current_user=current_user,
                organization_id=post.organization_id,
                action="post_scheduled",
                post_id=post.id,
                details={
                    "scheduled_at": post.scheduled_at.isoformat(),
                },
            )

        return post

    # =========================================================
    # PUBLISH POST NOW (Direct to Instagram)
    # Required Permission: publish.post
    # =========================================================
    def publish_post(
        self,
        db: Session,
        post_id: int,
        current_user,
        request: Request,
    ):
        post = self.get_post_record(
            db=db,
            post_id=post_id,
        )

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

        # 1. Connected Social Account Fetch
        account = None
        if post.social_account_id:
            account = (
                db.query(SocialAccount)
                .filter(SocialAccount.id == post.social_account_id)
                .first()
            )

        if not account:
            account = (
                db.query(SocialAccount)
                .filter(
                    SocialAccount.organization_id == post.organization_id,
                    SocialAccount.platform == "instagram",
                )
                .first()
            )

        if not account or not account.access_token:
            raise HTTPException(
                status_code=400,
                detail="No connected Instagram account found with valid access token",
            )

        # 2. Media Image URL Fetch
        if not post.media or len(post.media) == 0:
            raise HTTPException(
                status_code=400,
                detail="Instagram requires at least one image/media attached to the post",
            )

        media_url = post.media[0].url or post.media[0].file_path
        if not media_url.startswith("http"):
            # Relative path ko absolute URL banayein
            base_url = str(request.base_url).rstrip("/")
            media_url = f"{base_url}/{media_url.lstrip('/')}"

        # 3. Instagram Graph API Publish Process
        try:
            ig_user_id = account.account_id
            access_token = account.access_token

            # Step A: Container Create
            container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
            container_payload = {
                "image_url": media_url,
                "caption": post.caption or post.title or "",
                "access_token": access_token,
            }
            container_resp = httpx.post(container_url, data=container_payload, timeout=40.0)
            container_data = container_resp.json()

            if "id" not in container_data:
                err_msg = container_data.get("error", {}).get("message", str(container_data))
                raise HTTPException(
                    status_code=400,
                    detail=f"Instagram Media Creation Failed: {err_msg}",
                )

            creation_id = container_data["id"]

            # Step B: Publish Container
            publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": access_token,
            }
            publish_resp = httpx.post(publish_url, data=publish_payload, timeout=40.0)
            publish_data = publish_resp.json()

            if "id" not in publish_data:
                err_msg = publish_data.get("error", {}).get("message", str(publish_data))
                raise HTTPException(
                    status_code=400,
                    detail=f"Instagram Publish Failed: {err_msg}",
                )

            # Step C: Update Status to PUBLISHED
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
                    "instagram_post_id": publish_data.get("id"),
                    "platform": "instagram",
                },
            )

            return post

        except HTTPException:
            raise
        except Exception as err:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Publishing exception: {str(err)}",
            )

    # =========================================================
    # LIST POSTS
    # Required Permission: posts.view
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
            .filter(
                Post.organization_id == organization_id
            )
            .order_by(
                Post.created_at.desc()
            )
            .all()
        )

    # =========================================================
    # SINGLE POST DETAIL
    # Required Permission: posts.view
    # =========================================================
    def get_post_detail(
        self,
        db: Session,
        post_id: int,
        current_user,
    ):
        post = self.get_post_record(
            db=db,
            post_id=post_id,
        )

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
    # Required Permission: posts.update
    # =========================================================
    def update_post(
        self,
        db: Session,
        post_id: int,
        post_data,
        current_user,
        request: Request,
    ):
        post = self.get_post_record(
            db=db,
            post_id=post_id,
        )

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

        old_values = {
            "title": post.title,
            "caption": post.caption,
            "social_account_id": post.social_account_id,
            "scheduled_at": (
                post.scheduled_at.isoformat()
                if post.scheduled_at
                else None
            ),
            "status": post.status,
            "media_ids": [
                media.id
                for media in post.media
            ],
        }

        update_data = post_data.model_dump(
            exclude_unset=True,
        )

        media_ids = update_data.pop(
            "media_ids",
            None,
        )

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

        new_values = {
            "title": post.title,
            "caption": post.caption,
            "social_account_id": post.social_account_id,
            "scheduled_at": (
                post.scheduled_at.isoformat()
                if post.scheduled_at
                else None
            ),
            "status": post.status,
            "media_ids": [
                media.id
                for media in post.media
            ],
        }

        self.create_post_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=post.organization_id,
            action="post_updated",
            post_id=post.id,
            details={
                "old_values": old_values,
                "new_values": new_values,
                "updated_fields": (
                    list(update_data.keys())
                    + (
                        ["media_ids"]
                        if media_ids is not None
                        else []
                    )
                ),
            },
        )

        return post

    # =========================================================
    # DELETE POST
    # Required Permission: posts.delete
    # =========================================================
    def delete_post(
        self,
        db: Session,
        post_id: int,
        current_user,
        request: Request,
    ):
        post = self.get_post_record(
            db=db,
            post_id=post_id,
        )

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

        post_details = {
            "title": post.title,
            "caption": post.caption,
            "status": post.status,
            "social_account_id": post.social_account_id,
        }

        self.create_post_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=organization_id,
            action="post_deleted",
            post_id=deleted_post_id,
            details=post_details,
        )

        db.delete(post)
        db.commit()

        return {
            "success": True,
            "message": "Post deleted successfully",
        }

    # =========================================================
    # SCHEDULE POST
    # Required Permission: publish.post
    # =========================================================
    def schedule_post(
        self,
        db: Session,
        post_id: int,
        scheduled_at,
        current_user,
        request: Request,
    ):
        post = self.get_post_record(
            db=db,
            post_id=post_id,
        )

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

        old_scheduled_at = (
            post.scheduled_at.isoformat()
            if post.scheduled_at
            else None
        )

        post.scheduled_at = scheduled_at
        post.status = PostStatus.SCHEDULED.value

        db.commit()
        db.refresh(post)

        self.create_post_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=post.organization_id,
            action="post_scheduled",
            post_id=post.id,
            details={
                "old_scheduled_at": old_scheduled_at,
                "new_scheduled_at": (
                    post.scheduled_at.isoformat()
                ),
                "status": post.status,
            },
        )

        return post

    # =========================================================
    # ATTACH MEDIA TO POST
    # Required Permission: posts.update
    # =========================================================
    def attach_media_to_post(
        self,
        db: Session,
        post_id: int,
        data: AttachMediaRequest,
        current_user,
        request: Request,
    ):
        post = self.get_post_record(
            db=db,
            post_id=post_id,
        )

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

        existing_media_ids = {
            media.id
            for media in post.media
        }

        attached_media_ids = []

        for media in media_records:
            if media.id not in existing_media_ids:
                post.media.append(media)
                attached_media_ids.append(media.id)

        db.commit()
        db.refresh(post)

        self.create_post_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            organization_id=post.organization_id,
            action="media_attached_to_post",
            post_id=post.id,
            details={
                "attached_media_ids": attached_media_ids,
                "all_media_ids": [
                    media.id
                    for media in post.media
                ],
            },
        )

        return post