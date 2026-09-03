from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService


class NotificationService:

    def _create_audit_log(
        self,
        db: Session,
        request: Optional[Request],
        current_user: Optional[User],
        action: str,
        notification: Optional[Notification] = None,
        details: Optional[dict] = None,
    ):
        if current_user is None:
            return None

        audit_details = details or {}

        if notification is not None:
            audit_details.update(
                {
                    "notification_title": notification.title,
                    "notification_type": notification.notification_type,
                    "is_read": notification.is_read,
                }
            )

        return AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=None,
                action=action,
                entity_type="notification",
                entity_id=notification.id if notification else None,
                ip_address=(
                    request.client.host
                    if request and request.client
                    else None
                ),
                user_agent=(
                    request.headers.get("user-agent")
                    if request
                    else None
                ),
                details=audit_details,
            ),
        )

    def create_notification(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "general",
        request: Optional[Request] = None,
        current_user: Optional[User] = None,
    ):
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        self._create_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            action="notification_created",
            notification=notification,
        )

        return notification

    def get_notifications(
        self,
        db: Session,
        user_id: int,
    ):
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
        )

    def get_unread_count(
        self,
        db: Session,
        user_id: int,
    ):
        return (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .count()
        )

    def mark_as_read(
        self,
        db: Session,
        notification_id: int,
        user_id: int,
        request: Request,
        current_user: User,
    ):
        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )

        if not notification:
            return None

        was_already_read = notification.is_read

        notification.is_read = True

        db.commit()
        db.refresh(notification)

        self._create_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            action="notification_read",
            notification=notification,
            details={
                "was_already_read": was_already_read,
            },
        )

        return notification

    def mark_all_as_read(
        self,
        db: Session,
        user_id: int,
        request: Request,
        current_user: User,
    ):
        updated_count = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .update(
                {
                    "is_read": True,
                },
                synchronize_session=False,
            )
        )

        db.commit()

        self._create_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            action="notifications_read_all",
            details={
                "updated_count": updated_count,
            },
        )

        return updated_count

    def delete_notification(
        self,
        db: Session,
        notification_id: int,
        user_id: int,
        request: Request,
        current_user: User,
    ):
        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )

        if not notification:
            return False

        self._create_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            action="notification_deleted",
            notification=notification,
        )

        db.delete(notification)
        db.commit()

        return True