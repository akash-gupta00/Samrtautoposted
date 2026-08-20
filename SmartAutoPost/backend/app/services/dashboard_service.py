# SQLAlchemy aggregate functions import kar rahe hain.
from sqlalchemy import func

# Database session type import kar rahe hain.
from sqlalchemy.orm import Session

# Required models import kar rahe hain.
from app.models.post import Post
from app.models.publish_log import PublishLog
from app.models.social_account import SocialAccount
from app.models.ai_generation import AIGeneration


class DashboardService:
    """
    Dashboard se related saari business logic is service me rahegi.
    """

    @staticmethod
    def get_summary(
        db: Session,
        organization_id: int,
    ):
        """
        Dashboard ke summary cards ke counts return karega.
        """

        # Organization ke total posts count kar rahe hain.
        total_posts = (
            db.query(Post)
            .filter(Post.organization_id == organization_id)
            .count()
        )

        # Scheduled posts count kar rahe hain.
        scheduled_posts = (
            db.query(Post)
            .filter(
                Post.organization_id == organization_id,
                Post.status == "scheduled",
            )
            .count()
        )

        # Published posts count kar rahe hain.
        published_posts = (
            db.query(Post)
            .filter(
                Post.organization_id == organization_id,
                Post.status == "published",
            )
            .count()
        )

        # Failed publish attempts count kar rahe hain.
        failed_posts = (
            db.query(PublishLog)
            .join(Post, PublishLog.post_id == Post.id)
            .filter(
                Post.organization_id == organization_id,
                PublishLog.status == "failed",
            )
            .count()
        )

        # Active connected social accounts count kar rahe hain.
        connected_accounts = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.organization_id == organization_id,
                SocialAccount.is_active.is_(True),
            )
            .count()
        )

        # Successful AI generations count kar rahe hain.
        ai_generations = (
            db.query(AIGeneration)
            .filter(
                AIGeneration.organization_id == organization_id,
                AIGeneration.status == "success",
            )
            .count()
        )

        return {
            "total_posts": total_posts,
            "scheduled_posts": scheduled_posts,
            "published_posts": published_posts,
            "failed_posts": failed_posts,
            "connected_accounts": connected_accounts,
            "ai_generations": ai_generations,
        }

    @staticmethod
    def get_recent_posts(
        db: Session,
        organization_id: int,
        limit: int = 5,
    ):
        """
        Organization ke latest posts return karega.
        """

        # Latest posts ke saath unka social account provider bhi la rahe hain.
        rows = (
            db.query(
                Post,
                SocialAccount.provider,
            )
            .outerjoin(
                SocialAccount,
                Post.social_account_id == SocialAccount.id,
            )
            .filter(
                Post.organization_id == organization_id,
            )
            .order_by(
                Post.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

        recent_posts = []

        # Response schema ke according dictionary bana rahe hain.
        for post, provider in rows:
            recent_posts.append(
                {
                    "id": post.id,
                    "title": post.title,
                    "caption": post.caption,
                    "status": post.status,
                    "platform": provider,
                    "scheduled_at": post.scheduled_at,
                    "published_at": post.published_at,
                    "created_at": post.created_at,
                }
            )

        return recent_posts

    @staticmethod
    def get_recent_activity(
        db: Session,
        organization_id: int,
        limit: int = 10,
    ):
        """
        AI generation, publishing aur post creation ki latest
        activities ek combined list me return karega.
        """

        activities = []

        # Latest AI generation activities.
        ai_logs = (
            db.query(AIGeneration)
            .filter(
                AIGeneration.organization_id == organization_id,
            )
            .order_by(
                AIGeneration.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

        for log in ai_logs:
            activities.append(
                {
                    "activity_type": "ai",
                    "title": f"{log.generation_type.replace('_', ' ').title()} Generated",
                    "description": log.prompt,
                    "status": log.status,
                    "created_at": log.created_at,
                }
            )

        # Latest publishing activities.
        publish_logs = (
            db.query(PublishLog)
            .join(
                Post,
                PublishLog.post_id == Post.id,
            )
            .filter(
                Post.organization_id == organization_id,
            )
            .order_by(
                PublishLog.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

        for log in publish_logs:
            activities.append(
                {
                    "activity_type": "publish",
                    "title": f"Post {log.status.title()}",
                    "description": (
                        f"Post publish activity on {log.platform}"
                    ),
                    "status": log.status,
                    "created_at": log.created_at,
                }
            )

        # Latest post creation activities.
        posts = (
            db.query(Post)
            .filter(
                Post.organization_id == organization_id,
            )
            .order_by(
                Post.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

        for post in posts:
            # Caption ko maximum 80 characters tak dikha rahe hain.
            description = post.caption[:80]

            if len(post.caption) > 80:
                description += "..."

            activities.append(
                {
                    "activity_type": "post",
                    "title": f"Post Created: {post.title}",
                    "description": description,
                    "status": post.status,
                    "created_at": post.created_at,
                }
            )

        # Sabhi activities ko latest date ke according sort kar rahe hain.
        activities.sort(
            key=lambda activity: activity["created_at"],
            reverse=True,
        )

        # Requested limit ke according result return kar rahe hain.
        return activities[:limit]

    @staticmethod
    def get_dashboard_charts(
        db: Session,
        organization_id: int,
    ):
        """
        Dashboard ke status aur platform distribution charts
        ke liye data return karega.
        """

        # Post status ke according count nikal rahe hain.
        status_data = (
            db.query(
                Post.status,
                func.count(Post.id),
            )
            .filter(
                Post.organization_id == organization_id,
            )
            .group_by(
                Post.status,
            )
            .all()
        )

        posts_by_status = []

        for status, total in status_data:
            posts_by_status.append(
                {
                    "label": status or "unknown",
                    "value": total,
                }
            )

        # Publishing logs ko platform ke according count kar rahe hain.
        platform_data = (
            db.query(
                PublishLog.platform,
                func.count(PublishLog.id),
            )
            .join(
                Post,
                PublishLog.post_id == Post.id,
            )
            .filter(
                Post.organization_id == organization_id,
            )
            .group_by(
                PublishLog.platform,
            )
            .all()
        )

        platform_distribution = []

        for platform, total in platform_data:
            platform_distribution.append(
                {
                    "label": platform or "unknown",
                    "value": total,
                }
            )

        return {
            "posts_by_status": posts_by_status,
            "platform_distribution": platform_distribution,
        }