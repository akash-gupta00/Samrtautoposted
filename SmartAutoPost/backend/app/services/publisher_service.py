from datetime import datetime

from app.models.publish_log import PublishLog
from app.models.social_account import SocialAccount
from app.services.publish_service import PublishService


class PublisherService:
    """
    Scheduler aur Manual publish dono ke liye universal handler.
    Post me jude social_account ke platform ke anusar publish karega.
    """

    def __init__(self):
        try:
            self.publish_service = PublishService()
        except Exception:
            self.publish_service = None

    def publish_post(self, db, post, base_url: str = None, **kwargs):
        try:
            # 1. Social account verify karein
            if not post.social_account_id:
                # Agar post me directly social_account_id na ho toh org ka active account lein
                account = (
                    db.query(SocialAccount)
                    .filter(
                        SocialAccount.organization_id == post.organization_id,
                        SocialAccount.is_active == True,
                    )
                    .first()
                )
            else:
                account = (
                    db.query(SocialAccount)
                    .filter(
                        SocialAccount.id == post.social_account_id,
                        SocialAccount.is_active == True,
                    )
                    .first()
                )

            if not account:
                return {
                    "success": False,
                    "platform": None,
                    "error": "Connected social account nahi mila ya inactive hai",
                }

            # 2. Publish to platform (Instagram / Facebook / etc.)
            result = None
            if self.publish_service and hasattr(self.publish_service, "publish_to_platform"):
                try:
                    result = self.publish_service.publish_to_platform(
                        post=post,
                        social_account=account,
                        base_url=base_url,
                    )
                except TypeError:
                    result = self.publish_service.publish_to_platform(
                        post=post,
                        social_account=account,
                    )

            if not result:
                result = {"success": False, "error": "Publishing service unavailable"}

            # 3. Publish log record save karein
            publish_log = PublishLog(
                post_id=post.id,
                platform=result.get("platform", getattr(account, "provider", "instagram")),
                platform_post_id=result.get("platform_post_id") or result.get("instagram_post_id"),
                status="published" if result.get("success") else "failed",
                response=str(result),
            )
            db.add(publish_log)

            # 4. Status update karein
            if result.get("success"):
                post.status = "published"
                post.published_at = datetime.now()
            else:
                post.status = "failed"

            db.commit()
            db.refresh(post)

            return result

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "platform": None,
                "error": str(e),
            }