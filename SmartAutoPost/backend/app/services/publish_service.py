import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Post, SocialAccount, Organization
from app.providers.social.instagram_provider import InstagramProvider
# Agar Facebook / LinkedIn providers bhi hain to import karein:
# from app.providers.social.facebook_provider import FacebookProvider

logger = logging.getLogger(__name__)


class SocialPublishService:
    def __init__(self, db: Session):
        self.db = db

    def publish_post(self, post_id: int) -> dict:
        """
        Database se post aur associated social account ko load karke
        relevant platform par publish karta hai.
        """
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"success": False, "error": f"Post with id {post_id} not found."}

        # 1. Social Account Fetching Logic
        social_account = None
        if hasattr(post, "social_account_id") and post.social_account_id:
            social_account = self.db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()

        # Fallback: Agar direct link na ho to Organization ke primary account se fetch karein
        if not social_account and hasattr(post, "organization_id") and post.organization_id:
            social_account = (
                self.db.query(SocialAccount)
                .filter(SocialAccount.organization_id == post.organization_id)
                .first()
            )

        if not social_account:
            return {
                "success": False,
                "error": "No connected social account found for this post/workspace."
            }

        provider_name = str(social_account.provider).lower()
        access_token = str(social_account.access_token).strip()

        # 2. Instagram Publishing Flow
        if provider_name == "instagram":
            # Target ID Selection: Priority dijiye instagram_id -> page_id -> id
            target_ig_id = (
                getattr(social_account, "instagram_id", None)
                or getattr(social_account, "page_id", None)
                or getattr(social_account, "account_id", None)
                or getattr(social_account, "provider_user_id", None)
            )

            if not target_ig_id:
                return {
                    "success": False,
                    "error": "Instagram Business Account ID missing in database record."
                }

            logger.info(f"Publishing post {post.id} to Instagram ID: {target_ig_id}")

            provider = InstagramProvider(
                access_token=access_token,
                ig_user_id=str(target_ig_id)
            )

            # Publish trigger
            result = provider.publish_post(
                caption=post.caption or post.content or "",
                media_url=post.media_url
            )

            # 3. Post Status Update
            if result.get("success"):
                post.status = "PUBLISHED"
                if hasattr(post, "published_at"):
                    post.published_at = datetime.utcnow()
                if hasattr(post, "platform_post_id"):
                    post.platform_post_id = str(result.get("platform_post_id") or result.get("id"))
                self.db.commit()
                return {"success": True, "post_id": post.id, "platform_post_id": post.platform_post_id}
            else:
                post.status = "FAILED"
                if hasattr(post, "error_message"):
                    post.error_message = result.get("error")
                self.db.commit()
                return {"success": False, "error": result.get("error")}

        # 4. Other Providers (Facebook Page fallback)
        elif provider_name in ["facebook", "fb"]:
            # Facebook Page posting logic yahan daal sakte hain
            return {"success": False, "error": "Facebook publishing handler is not configured yet."}

        else:
            return {"success": False, "error": f"Unsupported social provider: {provider_name}"}