from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


notification_service = NotificationService()


@router.get(
    "/",
    response_model=list[NotificationResponse],
)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logged-in user ke saare notifications return karega.
    """

    return notification_service.get_notifications(
        db=db,
        user_id=current_user.id,
    )


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logged-in user ke unread notifications ka count return karega.
    """

    count = notification_service.get_unread_count(
        db=db,
        user_id=current_user.id,
    )

    return {
        "unread_count": count,
    }


@router.put("/read-all")
def mark_all_notifications_as_read(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logged-in user ke saare notifications ko read mark karega.
    """

    updated_count = notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id,
        request=request,
        current_user=current_user,
    )

    return {
        "success": True,
        "updated_count": updated_count,
        "message": "All notifications marked as read",
    }


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Specific notification ko read mark karega.
    """

    notification = notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
        request=request,
        current_user=current_user,
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Specific notification delete karega.
    """

    deleted = notification_service.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
        request=request,
        current_user=current_user,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {
        "success": True,
        "message": "Notification deleted successfully",
    }