import logging
from app.providers.social.instagram_provider import InstagramProvider

logger = logging.getLogger(__name__)


class PublishService:
    def __init__(self):
        pass

    def _extract_media_url(self, post, base_url: str = "") -> str | None:
        """
        Post object aur uski relationship (post.media) se valid public URL extract karta hai.
        """
        # 1. Direct post.media list check karein (Relationship)
        if hasattr(post, "media") and post.media:
            for item in post.media:
                url = getattr(item, "file_url", None) or getattr(item, "url", None)
                if url:
                    if url.startswith("http://") or url.startswith("https://"):
                        return url
                    clean_base = base_url.rstrip("/")
                    clean_path = url.lstrip("/")
                    return f"{clean_base}/{clean_path}"

        # 2. Direct post columns fallback
        direct_url = (
            getattr(post, "media_url", None)
            or getattr(post, "video_url", None)
            or getattr(post, "image_url", None)
        )
        if direct_url and str(direct_url).lower() != "none":
            if direct_url.startswith("http://") or direct_url.startswith("https://"):
                return direct_url
            clean_base = base_url.rstrip("/")
            clean_path = direct_url.lstrip("/")
            return f"{clean_base}/{clean_path}"

        return None

    def publish_to_platform(self, post, social_account) -> dict:
        try:
            provider_name = str(social_account.provider).lower()
            access_token = str(social_account.access_token).strip()

            # 1. Instagram Flow
            if provider_name == "instagram":
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

                # Media URL resolve karein
                base_domain = "https://samrtautoposted.onrender.com"
                media_url = self._extract_media_url(post, base_url=base_domain)

                if not media_url:
                    return {
                        "success": False,
                        "error": "Media URL (video/image) is required to publish to Instagram."
                    }

                caption_text = getattr(post, "caption", "") or getattr(post, "title", "") or ""

                logger.info(f"Publishing Post {post.id} to IG User {target_ig_id} with Media: {media_url}")

                provider = InstagramProvider(
                    access_token=access_token,
                    ig_user_id=str(target_ig_id)
                )

                result = provider.publish_post(
                    caption=caption_text,
                    media_url=media_url
                )

                return result

            # 2. Other Providers
            elif provider_name in ["facebook", "fb"]:
                return {"success": False, "error": "Facebook publishing not configured yet."}
            else:
                return {"success": False, "error": f"Unsupported platform: {provider_name}"}

        except Exception as e:
            logger.exception("Error during publish_to_platform")
            return {"success": False, "error": str(e)}