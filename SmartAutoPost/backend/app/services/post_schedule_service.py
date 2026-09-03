from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.enums import PostStatus
from app.models.post import Post
from app.models.post_schedule import PostSchedule
from app.repositories.post_schedule_repository import PostScheduleRepository
from app.schemas.audit_log import AuditLogCreate
from app.services.audit_log_service import AuditLogService
from app.services.publisher_service import PublisherService


class PostScheduleService:

    def __init__(self):
        self.repository = PostScheduleRepository()
        self.publisher = PublisherService()

    # Audit log create karega.
    def create_audit_log(
        self,
        db: Session,
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
                    user_id=current_user.id if current_user else 1,
                    organization_id=post.organization_id,
                    action=action,
                    entity_type="post_schedule",
                    entity_id=schedule.id if schedule else post.id,
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
            print(f"Schedule audit log error: {error}")

    # Schedule create karega.
    def create_schedule(
        self,
        db: Session,
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
        db: Session,
        schedule_id: int,
        schedule_time: datetime,
        current_user,
        request: Request,
    ):
        schedule = self.repository.get_by_id(db, schedule_id)

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
                "new_schedule_time": schedule.schedule_time.isoformat(),
                "status": schedule.status,
            },
        )

        return schedule

    # Schedule cancel karega.
    def cancel_schedule(
        self,
        db: Session,
        schedule_id: int,
        current_user,
        request: Request,
    ):
        schedule = self.repository.get_by_id(db, schedule_id)

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

        post.status = PostStatus.DRAFT.value
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
                "schedule_time": schedule.schedule_time.isoformat(),
            },
        )

        return schedule

    # =========================================================
    # PROCESS PENDING SCHEDULES (Direct Post Table + PostSchedule Sync)
    # =========================================================
    def process_pending_schedules(self, db: Session):
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        now_local = datetime.now()

        processed = 0
        failed = 0

        # Step 1: Check Direct Scheduled Posts from 'Post' table
        due_posts = (
            db.query(Post)
            .filter(
                Post.status == PostStatus.SCHEDULED.value,
                Post.scheduled_at.isnot(None),
                (Post.scheduled_at <= now_utc) | (Post.scheduled_at <= now_local),
            )
            .all()
        )

        for post in due_posts:
            try:
                # Direct publishing
                publish_result = self.publisher.publish_post(db=db, post=post)

                if isinstance(publish_result, dict) and publish_result.get("success") is False:
                    raise Exception(publish_result.get("error", "Publishing failed"))

                post.status = PostStatus.PUBLISHED.value
                db.commit()
                db.refresh(post)
                processed += 1
                print(f"✅ Automatically published post ID: {post.id} to Instagram")

            except Exception as error:
                db.rollback()
                print(f"❌ Auto-publish failed for post ID {post.id}: {error}")
                failed += 1

        # Step 2: Check PostSchedule records (if any created via specific queue)
        try:
            schedules = self.repository.list_pending_schedules(db, now_utc)
            for schedule in schedules:
                try:
                    post = db.query(Post).filter(Post.id == schedule.post_id).first()
                    if not post:
                        self.repository.update_status(db, schedule, "failed")
                        failed += 1
                        continue

                    self.repository.update_status(db, schedule, "processing")
                    publish_result = self.publisher.publish_post(db=db, post=post)

                    if isinstance(publish_result, dict) and publish_result.get("success") is False:
                        raise Exception(publish_result.get("error", "Publishing failed"))

                    self.repository.update_post_status(db, schedule.post_id, PostStatus.PUBLISHED.value)
                    self.repository.update_status(db, schedule, "published")
                    processed += 1

                except Exception as error:
                    db.rollback()
                    sch = self.repository.get_by_id(db, schedule.id)
                    if sch:
                        sch.retry_count += 1
                        sch.status = "failed"
                        db.commit()
                    failed += 1
        except Exception as e:
            print(f"PostSchedule table sync skip: {e}")

        return {
            "success": True,
            "processed": processed,
            "failed": failed,
        }