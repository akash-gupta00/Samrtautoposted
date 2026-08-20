from datetime import datetime

from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.organization_member import OrganizationMember


class CalendarService:

    def get_calendar_posts(
        self,
        db: Session,
        current_user,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):

        query = (
            db.query(Post)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Post.organization_id,
            )
            .filter(
                OrganizationMember.user_id == current_user.id,
                Post.scheduled_at.isnot(None),
            )
        )

        if start_date:
            query = query.filter(
                Post.scheduled_at >= start_date
            )

        if end_date:
            query = query.filter(
                Post.scheduled_at <= end_date
            )

        posts = (
            query
            .order_by(Post.scheduled_at.asc())
            .all()
        )

        return posts