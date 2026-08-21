import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Dynamic Models Import (Folder structure / Single file dono ke liye safe)
try:
    from app.models.post import Post
    from app.models.social_account import SocialAccount
    from app.models.organization import Organization
except ImportError:
    try:
        from app.models import Post, SocialAccount, Organization
    except ImportError:
        from app.models.models import Post, SocialAccount, Organization

from app.providers.social.instagram_provider import InstagramProvider

logger = logging.getLogger(__name__)


class PublishService:
    def __init__(self, db: Session):
        self.db = db

    def publish_post(self, post_id: int) -> dict:
        """
        Database se post aur linked Instagram account ko nikal kar
        direct Instagram Reel / Post publish karta hai.
        """
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"success": False, "error": f"Post with id {post_id} not found."}

        # 1. Social Account Link Resolve Karein
        social_account = None
        if hasattr(post, "social_account_id") and post.social_account_id:
            social_account = self.db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()

        if not social_account and hasattr(post, "organization_id") and post.organization_id:
            social_account = (
                self.db.query(SocialAccount)
                .filter(SocialAccount.organization_id == post.organization_id)
                .first()
            )

        if not social_account:
            return {
                "success": False,
                "error": "No connected social account found for this post."
            }

        provider_name = str(social_account.provider).lower()
        access_token = str(social_account.access_token).strip()

        # 2. Instagram Publishing Logic
        if provider_name == "instagram":
            # Priority ID Resolution: instagram_id -> page_id -> account_id
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

            logger.info(f"Publishing post {post.id} to Instagram Target ID: {target_ig_id}")

            provider = InstagramProvider(
                access_token=access_token,
                ig_user_id=str(target_ig_id)
            )

            # Execution
            caption_text = getattr(post, "caption", None) or getattr(post, "content", "") or ""
            media_url = getattr(post, "media_url", None) or getattr(post, "video_url", None) or getattr(post, "image_url", None)

            result = provider.publish_post(
                caption=caption_text,
                media_url=media_url
            )

            # 3. Status Update in Database
            if result.get("success"):
                post.status = "PUBLISHED"
                if hasattr(post, "published_at"):
                    post.published_at = datetime.utcnow()
                if hasattr(post, "platform_post_id"):
                    post.platform_post_id = str(result.get("platform_post_id") or result.get("id"))
                self.db.commit()
                return {"success": True, "post_id": post.id, "platform_post_id": getattr(post, "platform_post_id", None)}
            else:
                post.status = "FAILED"
                if hasattr(post, "error_message"):
                    post.error_message = result.get("error")
                self.db.commit()
                return {"success": False, "error": result.get("error")}

        # 4. Fallback for other providers
        else:
            return {"success": False, "error": f"Provider '{provider_name}' is not configured yet."}