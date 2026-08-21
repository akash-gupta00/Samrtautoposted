import logging
from app.providers.social.instagram_provider import InstagramProvider

logger = logging.getLogger(__name__)


class PublishService:
    def __init__(self):
        pass

    def publish_to_platform(self, post, social_account) -> dict:
        """
        API Router ke hisaab se post aur social_account object le kar
        Instagram / social platform par live content publish karta hai.
        """
        try:
            provider_name = str(social_account.provider).lower()
            access_token = str(social_account.access_token).strip()

            # 1. Instagram Publishing
            if provider_name == "instagram":
                # Instagram ID Priority Selection
                target_ig_id = (
                    getattr(social_account, "instagram_id", None)
                    or getattr(social_account, "page_id", None)
                    or getattr(social_account, "account_id", None)
                    or getattr(social_account, "provider_user_id", None)
                )

                if not target_ig_id:
                    return {
                        "success": False,
                        "error": "Instagram Business Account ID not found for this account."
                    }

                logger.info(f"Publishing post {post.id} to Instagram Target ID: {target_ig_id}")

                provider = InstagramProvider(
                    access_token=access_token,
                    ig_user_id=str(target_ig_id)
                )

                # Caption aur Media URL resolve karein
                caption_text = getattr(post, "caption", None) or getattr(post, "content", "") or ""
                media_url = (
                    getattr(post, "media_url", None)
                    or getattr(post, "video_url", None)
                    or getattr(post, "image_url", None)
                )

                if not media_url:
                    return {
                        "success": False,
                        "error": "Media URL (video/image) is required to publish to Instagram."
                    }

                # Trigger publish
                result = provider.publish_post(
                    caption=caption_text,
                    media_url=media_url
                )

                return result

            # 2. Other Providers (Facebook / LinkedIn)
            elif provider_name in ["facebook", "fb"]:
                return {
                    "success": False,
                    "error": "Facebook publishing is not configured yet."
                }

            else:
                return {
                    "success": False,
                    "error": f"Unsupported platform: {provider_name}"
                }

        except Exception as e:
            logger.exception("Error during publish_to_platform")
            return {
                "success": False,
                "error": str(e)
            }