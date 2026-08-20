from app.core.config import settings

from app.models.post import Post
from app.models.social_account import SocialAccount

from app.providers.social.facebook_provider import FacebookProvider
from app.providers.social.instagram_provider import InstagramProvider
from app.providers.social.linkedin_provider import LinkedInProvider


def resolve_media_url(post: Post):
    """
    Post ke sath attach hui pehli media file ka PUBLIC absolute
    URL banata hai (Facebook/Instagram/LinkedIn ke servers khud
    is URL ko fetch karte hain, isliye ye full https/http URL
    hona zaroori hai -- sirf relative path nahi).
    """
    if not post.media:
        return None

    first_media = post.media[0]
    file_url = first_media.file_url

    if not file_url:
        return None

    # Agar already absolute URL hai (http/https se shuru), waisa hi rehne do.
    if file_url.startswith("http://") or file_url.startswith("https://"):
        return file_url

    # Warna PUBLIC_BASE_URL ke sath jodkar absolute bana do.
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    path = file_url if file_url.startswith("/") else f"/{file_url}"

    return f"{base}{path}"


class PublishService:

    def publish_to_platform(
        self,
        post: Post,
        social_account: SocialAccount
    ):
        """
        Social account ke provider ke hisaab se REAL post publish karega.
        """

        try:
            platform = social_account.provider.lower().strip()

            caption = post.caption
            media_url = resolve_media_url(post)

            if platform == "facebook":
                provider = FacebookProvider(
                    access_token=social_account.access_token,
                    page_id=social_account.page_id,
                )
                result = provider.publish_post(caption, media_url)

            elif platform == "instagram":
                provider = InstagramProvider(
                    access_token=social_account.access_token,
                    ig_user_id=social_account.page_id,
                )
                result = provider.publish_post(caption, media_url)

            elif platform == "linkedin":
                provider = LinkedInProvider(
                    access_token=social_account.access_token,
                    author_urn=social_account.page_id,
                )
                result = provider.publish_post(caption, media_url)

            else:
                # Threads ya koi aur platform abhi support nahi hai --
                # honest error dete hain, fake success nahi.
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
