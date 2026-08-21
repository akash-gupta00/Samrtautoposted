from app.core.config import settings
from app.models.post import Post
from app.models.social_account import SocialAccount

from app.providers.social.facebook_provider import FacebookProvider
from app.providers.social.instagram_provider import InstagramProvider
from app.providers.social.linkedin_provider import LinkedInProvider


def resolve_media_url(post: Post, custom_base: str = None):
    if not post.media:
        return None

    first_media = post.media[0]
    file_url = (
        getattr(first_media, "file_url", None)
        or getattr(first_media, "url", None)
        or getattr(first_media, "file_path", None)
    )

    if not file_url:
        return None

    live_host = (
        custom_base
        or getattr(settings, "PUBLIC_BASE_URL", "https://samrtautoposted.onrender.com")
        or "https://samrtautoposted.onrender.com"
    )
    live_host = live_host.rstrip("/")

    if not (file_url.startswith("http://") or file_url.startswith("https://")):
        path = file_url if file_url.startswith("/") else f"/{file_url}"
        file_url = f"{live_host}{path}"

    file_url = file_url.replace("smartautopost.onrender.com", "samrtautoposted.onrender.com")

    if file_url.startswith("http://"):
        file_url = file_url.replace("http://", "https://")

    return file_url


class PublishService:

    def publish_to_platform(
        self,
        post: Post,
        social_account: SocialAccount,
        base_url: str = None,
        **kwargs
    ):
        try:
            platform = str(getattr(social_account, "platform", None) or getattr(social_account, "provider", "instagram")).lower().strip()
            caption = post.caption or post.title or ""
            media_url = resolve_media_url(post, custom_base=base_url)

            if platform == "facebook":
                provider = FacebookProvider(
                    access_token=social_account.access_token,
                    page_id=social_account.page_id or getattr(social_account, "account_id", None),
                )
                result = provider.publish_post(caption, media_url)

            elif platform in ["instagram", "ig"]:
                ig_id = (
                    getattr(social_account, "account_id", None)
                    or getattr(social_account, "page_id", None)
                    or getattr(social_account, "platform_account_id", None)
                )
                provider = InstagramProvider(
                    access_token=social_account.access_token,
                    ig_user_id=ig_id,
                )
                result = provider.publish_post(caption, media_url)

            elif platform == "linkedin":
                provider = LinkedInProvider(
                    access_token=social_account.access_token,
                    author_urn=getattr(social_account, "page_id", None) or getattr(social_account, "account_id", None),
                )
                result = provider.publish_post(caption, media_url)

            else:
                result = {
                    "success": False,
                    "error": f"'{platform}' abhi publish ke liye supported nahi hai.",
                }

            if not isinstance(result, dict):
                result = {"success": True, "id": str(result)}

            # Standardize Post ID Extraction across any response format
            platform_id = (
                result.get("id")
                or result.get("platform_post_id")
                or result.get("instagram_post_id")
                or result.get("media_id")
                or result.get("post_id")
            )

            if platform_id:
                result["platform_post_id"] = str(platform_id)
                result["instagram_post_id"] = str(platform_id)
                result["success"] = True

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }