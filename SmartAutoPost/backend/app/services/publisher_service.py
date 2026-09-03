from datetime import datetime
import json
from app.models.publish_log import PublishLog
from app.models.social_account import SocialAccount
from app.services.publish_service import PublishService


class PublisherService:
    """
    Universal Scheduler & Manual Multi-Platform Publish Handler.
    """

    def __init__(self):
        try:
            self.publish_service = PublishService()
        except Exception:
            self.publish_service = None

    def publish_post(self, db, post, base_url: str = None, **kwargs):
        try:
            # 1. Social account fetch karein
            account = None
            if getattr(post, "social_account_id", None):
                account = (
                    db.query(SocialAccount)
                    .filter(
                        SocialAccount.id == post.social_account_id,
                        SocialAccount.is_active == True,
                    )
                    .first()
                )
            
            # Fallback check
            if not account and getattr(post, "organization_id", None):
                account = (
                    db.query(SocialAccount)
                    .filter(
                        SocialAccount.organization_id == post.organization_id,
                        SocialAccount.is_active == True,
                    )
                    .first()
                )

            if not account:
                return {
                    "success": False,
                    "platform": None,
                    "error": f"Connected social account (ID: {getattr(post, 'social_account_id', 'N/A')}) nahi mila ya inactive hai",
                }

            # 2. Publish to specific platform
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

            # 3. Platform Specific ID extraction (Instagram, Facebook, GMB, LinkedIn)
            platform_id = None
            if isinstance(result, dict):
                data_obj = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
                platform_id = (
                    result.get("post_id")
                    or result.get("platform_post_id") 
                    or result.get("instagram_post_id") 
                    or result.get("google_post_id")
                    or result.get("media_id")
                    or result.get("id")
                    or data_obj.get("id")
                    or data_obj.get("name") # Google Business Profile Post Name/ID
                )

            provider_name = getattr(account, "provider", "unknown")
            is_success = bool(result.get("success", False))

            # 4. Publish log record save karein
            publish_log = PublishLog(
                post_id=post.id,
                platform=result.get("platform", provider_name),
                platform_post_id=str(platform_id) if platform_id else None,
                status="published" if is_success else "failed",
                response=json.dumps(result) if isinstance(result, dict) else str(result),
            )
            db.add(publish_log)

            # 5. Post Table Status & Timestamp update karein
            if is_success:
                post.status = "published"
                post.published_at = datetime.utcnow()
                
                if platform_id:
                    if hasattr(post, "platform_post_id"):
                        post.platform_post_id = str(platform_id)
                    if hasattr(post, "ig_media_id"):
                        post.ig_media_id = str(platform_id)
                    if hasattr(post, "external_id"):
                        post.external_id = str(platform_id)
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