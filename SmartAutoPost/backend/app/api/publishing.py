from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user

from app.models.user import User
from app.models.post import Post
from app.models.social_account import SocialAccount
from app.models.publish_log import PublishLog
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember

from app.schemas.publish import (
    PublishResponse,
    PublishLogResponse,
)
from app.schemas.audit_log import AuditLogCreate

from app.services.publish_service import PublishService
from app.services.notification_service import NotificationService
from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/publish",
    tags=["Publishing"],
)


publish_service = PublishService()
notification_service = NotificationService()


# User ko post ka access hai ya nahi check karega.
def get_accessible_post(
    db: Session,
    post_id: int,
    current_user: User,
):
    post = (
        db.query(Post)
        .join(
            Organization,
            Organization.id == Post.organization_id,
        )
        .outerjoin(
            OrganizationMember,
            OrganizationMember.organization_id
            == Post.organization_id,
        )
        .filter(
            Post.id == post_id,
            (
                (Organization.owner_id == current_user.id)
                | (OrganizationMember.user_id == current_user.id)
            ),
        )
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found or you do not have access",
        )

    return post


# Publish log database me save karega.
def save_publish_log(
    db: Session,
    post_id: int,
    provider: str,
    log_status: str,
    result: dict,
):
    log = PublishLog(
        post_id=post_id,
        platform=provider,
        platform_post_id=result.get("platform_post_id"),
        status=log_status,
        response=str(result),
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


# Publishing actions ka audit log create karega.
def create_publish_audit_log(
    db: Session,
    request: Request,
    current_user: User,
    post: Post,
    action: str,
    details: dict | None = None,
):
    try:
        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=post.organization_id,
                action=action,
                entity_type="post",
                entity_id=post.id,
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
        print(f"Publish audit log error: {error}")


@router.post(
    "/{post_id}",
    response_model=PublishResponse,
)
def publish_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = get_accessible_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post already published",
        )

    if post.social_account_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No social account attached to this post",
        )

    social_account = (
        db.query(SocialAccount)
        .filter(
            SocialAccount.id == post.social_account_id,
            SocialAccount.organization_id
            == post.organization_id,
        )
        .first()
    )

    if not social_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Social account not found",
        )

    if not social_account.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Social account is not active",
        )

    # Publish start hone ka audit log.
    create_publish_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        post=post,
        action="post_publish_started",
        details={
            "title": post.title,
            "platform": social_account.provider,
            "social_account_id": social_account.id,
        },
    )

    try:
        result = publish_service.publish_to_platform(
            post=post,
            social_account=social_account,
        )

    except Exception as error:
        db.rollback()

        post.status = "failed"
        db.commit()
        db.refresh(post)

        failed_result = {
            "success": False,
            "error": str(error),
        }

        save_publish_log(
            db=db,
            post_id=post.id,
            provider=social_account.provider,
            log_status="failed",
            result=failed_result,
        )

        create_publish_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            post=post,
            action="post_publish_failed",
            details={
                "platform": social_account.provider,
                "error": str(error),
            },
        )

        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            title="Post Publishing Failed",
            message=(
                f'Your post "{post.title}" '
                "could not be published."
            ),
            notification_type="post_failed",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )

    # Publish service ne failure response diya.
    if not result.get("success"):
        post.status = "failed"

        db.commit()
        db.refresh(post)

        save_publish_log(
            db=db,
            post_id=post.id,
            provider=social_account.provider,
            log_status="failed",
            result=result,
        )

        create_publish_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            post=post,
            action="post_publish_failed",
            details={
                "platform": social_account.provider,
                "error": result.get(
                    "error",
                    "Publishing failed",
                ),
                "result": result,
            },
        )

        notification_service.create_notification(
            db=db,
            user_id=current_user.id,
            title="Post Publishing Failed",
            message=(
                f'Your post "{post.title}" '
                "could not be published."
            ),
            notification_type="post_failed",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get(
                "error",
                "Publishing failed",
            ),
        )

    # Publish successful.
    post.status = "published"
    post.published_at = datetime.utcnow()

    if hasattr(post, "platform_post_id"):
        post.platform_post_id = result.get(
            "platform_post_id"
        )

    db.commit()
    db.refresh(post)

    save_publish_log(
        db=db,
        post_id=post.id,
        provider=social_account.provider,
        log_status="published",
        result=result,
    )

    create_publish_audit_log(
        db=db,
        request=request,
        current_user=current_user,
        post=post,
        action="post_publish_success",
        details={
            "title": post.title,
            "platform": social_account.provider,
            "platform_post_id": result.get(
                "platform_post_id"
            ),
            "published_at": (
                post.published_at.isoformat()
                if post.published_at
                else None
            ),
        },
    )

    notification_service.create_notification(
        db=db,
        user_id=current_user.id,
        title="Post Published",
        message=(
            f'Your post "{post.title}" '
            "was published successfully."
        ),
        notification_type="post_published",
    )

    return {
        "success": True,
        "message": "Post published successfully",
        "platform": social_account.provider,
        "platform_post_id": result.get(
            "platform_post_id"
        ),
        "published_at": post.published_at,
    }


@router.post(
    "/retry/{post_id}",
    response_model=PublishResponse,
)
def retry_publish(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = get_accessible_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

    if post.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed posts can be retried",
        )

    return publish_post(
        post_id=post_id,
        request=request,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/logs/{post_id}",
    response_model=list[PublishLogResponse],
)
def get_publish_logs(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = get_accessible_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

    logs = (
        db.query(PublishLog)
        .filter(PublishLog.post_id == post.id)
        .order_by(PublishLog.created_at.desc())
        .all()
    )

    return logs


@router.get("/status/{post_id}")
def get_publish_status(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = get_accessible_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )

    social_account = None

    if post.social_account_id is not None:
        social_account = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.id
                == post.social_account_id,
                SocialAccount.organization_id
                == post.organization_id,
            )
            .first()
        )

    return {
        "success": True,
        "post_id": post.id,
        "status": post.status,
        "platform": (
            social_account.provider
            if social_account
            else None
        ),
        "platform_post_id": getattr(
            post,
            "platform_post_id",
            None,
        ),
        "published_at": post.published_at,
    }