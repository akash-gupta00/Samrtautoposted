import logging
import requests
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

    def _publish_facebook(self, page_id: str, access_token: str, caption: str, media_url: str | None) -> dict:
        """
        Facebook Graph API Post Handler (Photo, Video/Reels, and Text)
        """
        base_api = f"https://graph.facebook.com/v20.0/{page_id}"

        # 1. Video / Reel Publishing
        if media_url and any(media_url.lower().split("?")[0].endswith(ext) for ext in [".mp4", ".mov", ".m4v", ".webm", ".avi"]):
            logger.info(f"Publishing Video/Reel to Facebook Page {page_id}")
            res = requests.post(
                f"{base_api}/videos",
                data={
                    "access_token": access_token,
                    "description": caption,
                    "file_url": media_url
                },
                timeout=60
            )
            data = res.json()
            if "id" in data:
                return {"success": True, "post_id": data["id"]}
            return {"success": False, "error": data.get("error", {}).get("message", "Facebook video upload failed")}

        # 2. Photo Publishing
        elif media_url:
            logger.info(f"Publishing Photo to Facebook Page {page_id}")
            res = requests.post(
                f"{base_api}/photos",
                data={
                    "access_token": access_token,
                    "caption": caption,
                    "url": media_url
                },
                timeout=30
            )
            data = res.json()
            if "id" in data or "post_id" in data:
                return {"success": True, "post_id": data.get("post_id") or data.get("id")}
            return {"success": False, "error": data.get("error", {}).get("message", "Facebook photo upload failed")}

        # 3. Feed Text Post
        else:
            logger.info(f"Publishing Feed post to Facebook Page {page_id}")
            res = requests.post(
                f"{base_api}/feed",
                data={
                    "access_token": access_token,
                    "message": caption
                },
                timeout=30
            )
            data = res.json()
            if "id" in data:
                return {"success": True, "post_id": data["id"]}
            return {"success": False, "error": data.get("error", {}).get("message", "Facebook feed post failed")}

    def publish_to_platform(self, post, social_account) -> dict:
        try:
            provider_name = str(social_account.provider).lower()
            access_token = str(social_account.access_token).strip()
            base_domain = "https://samrtautoposted.onrender.com"
            media_url = self._extract_media_url(post, base_url=base_domain)
            caption_text = getattr(post, "caption", "") or getattr(post, "title", "") or ""

            # 1. Instagram Flow (Untouched)
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

                if not media_url:
                    return {
                        "success": False,
                        "error": "Media URL (video/image) is required to publish to Instagram."
                    }

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

            # 2. Facebook Flow (Live API Publishing)
            elif provider_name in ["facebook", "fb"]:
                target_fb_id = getattr(social_account, "page_id", None) or getattr(social_account, "account_id", None)
                if not target_fb_id:
                    return {
                        "success": False,
                        "error": "Facebook Page ID missing."
                    }

                return self._publish_facebook(
                    page_id=str(target_fb_id),
                    access_token=access_token,
                    caption=caption_text,
                    media_url=media_url
                )

            else:
                return {"success": False, "error": f"Unsupported platform: {provider_name}"}

        except Exception as e:
            logger.exception("Error during publish_to_platform")
            return {"success": False, "error": str(e)}