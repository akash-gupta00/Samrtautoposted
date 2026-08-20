from app.models.post_schedule import PostSchedule
from app.models.post import Post


class PostScheduleRepository:

    # Naya schedule create karega.
    def create(self, db, schedule):
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return schedule

    # Schedule ID se schedule nikalega.
    def get_by_id(self, db, schedule_id: int):
        return (
            db.query(PostSchedule)
            .filter(PostSchedule.id == schedule_id)
            .first()
        )

    # Multiple posts ke schedules nikalega.
    def list_by_post_ids(self, db, post_ids: list[int]):
        return (
            db.query(PostSchedule)
            .filter(PostSchedule.post_id.in_(post_ids))
            .all()
        )

    # Pending schedules nikalega.
    def list_pending_schedules(self, db, current_time):
        return (
            db.query(PostSchedule)
            .filter(
                PostSchedule.status == "pending",
                PostSchedule.schedule_time <= current_time,
            )
            .all()
        )

    # Schedule ka time update karega.
    def update_schedule_time(
        self,
        db,
        schedule: PostSchedule,
        schedule_time,
    ):
        schedule.schedule_time = schedule_time
        schedule.status = "pending"

        db.commit()
        db.refresh(schedule)

        return schedule

    # Schedule cancel karega.
    def cancel_schedule(
        self,
        db,
        schedule: PostSchedule,
    ):
        schedule.status = "cancelled"

        db.commit()
        db.refresh(schedule)

        return schedule

    # Schedule status update karega.
    def update_status(
        self,
        db,
        schedule: PostSchedule,
        status: str,
    ):
        schedule.status = status

        db.commit()
        db.refresh(schedule)

        return schedule

    # Post status update karega.
    def update_post_status(
        self,
        db,
        post_id: int,
        status: str,
    ):
        post = (
            db.query(Post)
            .filter(Post.id == post_id)
            .first()
        )

        if post:
            post.status = status

            db.commit()
            db.refresh(post)

        return post