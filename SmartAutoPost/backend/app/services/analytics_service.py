from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.social_account import SocialAccount
from app.models.organization_member import OrganizationMember


class AnalyticsService:

    def get_summary(
        self,
        db: Session,
        current_user,
    ):

        organization_ids = (
            db.query(OrganizationMember.organization_id)
            .filter(
                OrganizationMember.user_id == current_user.id
            )
            .subquery()
        )

        total_posts = (
            db.query(Post)
            .filter(
                Post.organization_id.in_(
                    organization_ids
                )
            )
            .count()
        )

        draft_posts = (
            db.query(Post)
            .filter(
                Post.organization_id.in_(
                    organization_ids
                ),
                Post.status == "draft",
            )
            .count()
        )

        scheduled_posts = (
            db.query(Post)
            .filter(
                Post.organization_id.in_(
                    organization_ids
                ),
                Post.scheduled_at.isnot(None),
                Post.status != "published",
            )
            .count()
        )

        published_posts = (
            db.query(Post)
            .filter(
                Post.organization_id.in_(
                    organization_ids
                ),
                Post.status == "published",
            )
            .count()
        )

        failed_posts = (
            db.query(Post)
            .filter(
                Post.organization_id.in_(
                    organization_ids
                ),
                Post.status == "failed",
            )
            .count()
        )

        connected_accounts = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.organization_id.in_(
                    organization_ids
                ),
                SocialAccount.is_active.is_(True),
            )
            .count()
        )

        return {
            "total_posts": total_posts,
            "draft_posts": draft_posts,
            "scheduled_posts": scheduled_posts,
            "published_posts": published_posts,
            "failed_posts": failed_posts,
            "connected_accounts": connected_accounts,
        }