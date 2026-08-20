from datetime import datetime

from fastapi import HTTPException, Request

from app.models.post import Post
from app.models.post_schedule import PostSchedule

from app.core.enums import PostStatus

from app.repositories.post_schedule_repository import (
    PostScheduleRepository,
)

from app.services.publisher_service import PublisherService
from app.services.audit_log_service import AuditLogService

from app.schemas.audit_log import AuditLogCreate


class PostScheduleService:

    def __init__(self):
        self.repository = PostScheduleRepository()
        self.publisher = PublisherService()

    # Audit log create karega.
    def create_audit_log(
        self,
        db,
        request: Request,
        current_user,
        post: Post,
        schedule: PostSchedule,
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
                    entity_type="post_schedule",
                    entity_id=schedule.id,
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
            print(f"Schedule audit log error: {error}")

    # Schedule create karega.
    def create_schedule(
        self,
        db,
        data,
        current_user,
        request: Request,
    ):
        post = (
            db.query(Post)
            .filter(Post.id == data.post_id)
            .first()
        )

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Post not found",
            )

        schedule = PostSchedule(
            post_id=data.post_id,
            schedule_time=data.schedule_time,
            timezone=data.timezone,
            status="pending",
        )

        post.status = PostStatus.SCHEDULED.value

        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        db.refresh(post)

        self.create_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            post=post,
            schedule=schedule,
            action="schedule_created",
            details={
                "post_id": post.id,
                "schedule_time": schedule.schedule_time.isoformat(),
                "timezone": schedule.timezone,
                "status": schedule.status,
            },
        )

        return schedule

    # Schedule time update karega.
    def reschedule_post(
        self,
        db,
        schedule_id: int,
        schedule_time: datetime,
        current_user,
        request: Request,
    ):
        schedule = self.repository.get_by_id(
            db,
            schedule_id,
        )

        if not schedule:
            raise HTTPException(
                status_code=404,
                detail="Schedule not found",
            )

        post = (
            db.query(Post)
            .filter(Post.id == schedule.post_id)
            .first()
        )

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Post not found",
            )

        if post.organization_id is None:
            raise HTTPException(
                status_code=400,
                detail="Post organization not found",
            )

        old_schedule_time = schedule.schedule_time

        schedule = self.repository.update_schedule_time(
            db=db,
            schedule=schedule,
            schedule_time=schedule_time,
        )

        post.status = PostStatus.SCHEDULED.value
        db.commit()
        db.refresh(post)

        self.create_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            post=post,
            schedule=schedule,
            action="schedule_updated",
            details={
                "post_id": post.id,
                "old_schedule_time": (
                    old_schedule_time.isoformat()
                    if old_schedule_time
                    else None
                ),
                "new_schedule_time": (
                    schedule.schedule_time.isoformat()
                ),
                "status": schedule.status,
            },
        )

        return schedule

    # Schedule cancel karega.
    def cancel_schedule(
        self,
        db,
        schedule_id: int,
        current_user,
        request: Request,
    ):
        schedule = self.repository.get_by_id(
            db,
            schedule_id,
        )

        if not schedule:
            raise HTTPException(
                status_code=404,
                detail="Schedule not found",
            )

        post = (
            db.query(Post)
            .filter(Post.id == schedule.post_id)
            .first()
        )

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Post not found",
            )

        if schedule.status == "cancelled":
            raise HTTPException(
                status_code=400,
                detail="Schedule already cancelled",
            )

        old_status = schedule.status

        schedule = self.repository.cancel_schedule(
            db=db,
            schedule=schedule,
        )

        post.status = "draft"
        db.commit()
        db.refresh(post)

        self.create_audit_log(
            db=db,
            request=request,
            current_user=current_user,
            post=post,
            schedule=schedule,
            action="schedule_cancelled",
            details={
                "post_id": post.id,
                "old_status": old_status,
                "new_status": schedule.status,
                "schedule_time": (
                    schedule.schedule_time.isoformat()
                ),
            },
        )

        return schedule

    # Pending schedules process karega.
    def process_pending_schedules(self, db):
        current_time = datetime.now()

        schedules = self.repository.list_pending_schedules(
            db,
            current_time,
        )

        processed = 0
        failed = 0

        for schedule in schedules:
            try:
                post = (
                    db.query(Post)
                    .filter(Post.id == schedule.post_id)
                    .first()
                )

                if not post:
                    self.repository.update_status(
                        db,
                        schedule,
                        "failed",
                    )
                    failed += 1
                    continue

                # Pehle processing status.
                self.repository.update_status(
                    db,
                    schedule,
                    "processing",
                )

                # Sirf ek baar publish call hoga.
                publish_result = self.publisher.publish_post(
                    db=db,
                    post=post,
                )

                if (
                    isinstance(publish_result, dict)
                    and publish_result.get("success") is False
                ):
                    raise Exception(
                        publish_result.get(
                            "error",
                            "Publishing failed",
                        )
                    )

                self.repository.update_post_status(
                    db,
                    schedule.post_id,
                    PostStatus.PUBLISHED.value,
                )

                self.repository.update_status(
                    db,
                    schedule,
                    "published",
                )

                processed += 1

            except Exception as error:
                db.rollback()

                schedule = self.repository.get_by_id(
                    db,
                    schedule.id,
                )

                if schedule:
                    schedule.retry_count += 1
                    schedule.status = "failed"

                    db.commit()
                    db.refresh(schedule)

                print(
                    f"Schedule {schedule.id} failed: {error}"
                )

                failed += 1

        return {
            "success": True,
            "processed": processed,
            "failed": failed,
        }