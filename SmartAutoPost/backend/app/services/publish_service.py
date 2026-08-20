from app.core.config import settings
from app.models.post import Post
from app.models.social_account import SocialAccount

from app.providers.social.facebook_provider import FacebookProvider
from app.providers.social.instagram_provider import InstagramProvider
from app.providers.social.linkedin_provider import LinkedInProvider


def resolve_media_url(post: Post, custom_base: str = None):
    """
    Post ke sath attach hui media file ka live public URL banata hai.
    Galat/purane render domains ko auto-replace karke actual live URL set karta hai.
    """
    if not post.media:
        return None

    first_media = post.media[0]
    
    # Har tarah ke possible model attributes check karein
    file_url = getattr(first_media, "file_url", None) or getattr(first_media, "url", None) or getattr(first_media, "file_path", None)

    if not file_url:
        return None

    # Base URL determine karein
    live_host = custom_base or getattr(settings, "PUBLIC_BASE_URL", "https://samrtautoposted.onrender.com") or "https://samrtautoposted.onrender.com"
    live_host = live_host.rstrip("/")

    # Agar relative path hai toh absolute banayein
    if not (file_url.startswith("http://") or file_url.startswith("https://")):
        path = file_url if file_url.startswith("/") else f"/{file_url}"
        file_url = f"{live_host}{path}"

    # Purana galat domain auto-replace karein
    file_url = file_url.replace("smartautopost.onrender.com", "samrtautoposted.onrender.com")

    # Facebook/Instagram strictly https expect karte hain
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
        """
        Social account ke provider ke hisaab se REAL post publish karega.
        """
        try:
            platform = social_account.provider.lower().strip()
            caption = post.caption or post.title or ""
            media_url = resolve_media_url(post, custom_base=base_url)

            if platform == "facebook":
                provider = FacebookProvider(
                    access_token=social_account.access_token,
                    page_id=social_account.page_id or social_account.account_id,
                )
                result = provider.publish_post(caption, media_url)

            elif platform == "instagram":
                # Instagram business ID target karein
                ig_id = getattr(social_account, "page_id", None) or getattr(social_account, "account_id", None)
                provider = InstagramProvider(
                    access_token=social_account.access_token,
                    ig_user_id=ig_id,
                )
                result = provider.publish_post(caption, media_url)

            elif platform == "linkedin":
                provider = LinkedInProvider(
                    access_token=social_account.access_token,
                    author_urn=social_account.page_id or social_account.account_id,
                )
                result = provider.publish_post(caption, media_url)

            else:
                result = {
                    "success": False,
                    "error": f"'{platform}' abhi publish ke liye supported nahi hai.",
                }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }