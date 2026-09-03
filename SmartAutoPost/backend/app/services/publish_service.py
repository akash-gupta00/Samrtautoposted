import logging
import os
import json
import re
import requests
from app.providers.social.instagram_provider import InstagramProvider
from app.providers.social.facebook_provider import FacebookProvider
from app.providers.social.gmb_provider import GoogleBusinessProvider

logger = logging.getLogger(__name__)


def optimize_caption_for_platform(caption: str, platform: str) -> str:
    """
    Platform ke rules ke mutabiq caption, hashtags aur mentions optimize karta hai.
    """
    if not caption:
        return ""
    
    platform = str(platform).lower()
    text = caption.strip()

    # 1. GOOGLE BUSINESS PROFILE (GMB) - No raw hashtags or @mentions
    if "google" in platform or "gmb" in platform:
        text = re.sub(r'#(\w+)', r'\1', text)
        text = re.sub(r'@(\w+)', r'\1', text)
        return text.strip()

    # 2. LINKEDIN - Max 3-4 professional hashtags at the end
    elif "linkedin" in platform:
        words = text.split()
        body_words = [w for w in words if not w.startswith("#")]
        hashtag_words = [w for w in words if w.startswith("#")]
        main_text = " ".join(body_words).strip()
        selected_tags = hashtag_words[:4]
        if selected_tags:
            return f"{main_text}\n\n{' '.join(selected_tags)}".strip()
        return main_text

    # 3. FACEBOOK - Max 2 hashtags
    elif "facebook" in platform or "fb" in platform:
        words = text.split()
        body_words = [w for w in words if not w.startswith("#")]
        hashtag_words = [w for w in words if w.startswith("#")]
        main_text = " ".join(body_words).strip()
        selected_tags = hashtag_words[:2]
        if selected_tags:
            return f"{main_text}\n\n{' '.join(selected_tags)}".strip()
        return main_text

    # 4. INSTAGRAM - Keep all tags & format intact
    elif "instagram" in platform or "ig" in platform:
        return text

    return text


class PublishService:
    def __init__(self):
        pass

    def _extract_media_url(self, post, db=None, base_url: str = "") -> str | None:
        """
        Direct attributes, media relation aur database se public absolute URL banata hai.
        """
        domain = base_url.rstrip("/") if (base_url and str(base_url).strip()) else "https://samrtautoposted.onrender.com"
        raw_target = None

        # 1. Direct Post attributes check
        for attr in ["media_url", "image_url", "video_url", "file_url"]:
            val = getattr(post, attr, None)
            if val and str(val).strip().lower() not in ["none", "null", ""]:
                raw_target = str(val).strip()
                break

        # 2. post.media relationship check
        if not raw_target:
            media_items = getattr(post, "media", None)
            if media_items:
                for item in media_items:
                    val = (
                        getattr(item, "file_url", None)
                        or getattr(item, "url", None)
                        or getattr(item, "file_path", None)
                    )
                    if val and str(val).strip().lower() not in ["none", "null", ""]:
                        raw_target = str(val).strip()
                        break

        # 3. Build Clean Absolute URL
        if raw_target:
            if raw_target.startswith("http://") or raw_target.startswith("https://"):
                return raw_target
            clean_path = raw_target.lstrip("/")
            return f"{domain}/{clean_path}"

        return None

    def publish_to_platform(self, post, social_account=None, db=None, base_url: str = "") -> dict:
        """
        Facebook, Instagram, Google Business Profile aur LinkedIn par optimized content dispatch karta hai.
        """
        try:
            # 1. Ensure Social Account is loaded dynamically
            if not social_account and getattr(post, "social_account_id", None) and db:
                from app.models.social_account import SocialAccount
                social_account = db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()

            # 2. Strict Platform & Provider Detection
            provider_str = ""
            if social_account and getattr(social_account, "provider", None):
                provider_str = str(social_account.provider).lower()
            elif hasattr(post, "platform") and post.platform:
                provider_str = str(post.platform).lower()

            if "google" in provider_str or "gmb" in provider_str or (social_account and getattr(social_account, "location_id", None)):
                provider_name = "google_business"
            elif "linkedin" in provider_str:
                provider_name = "linkedin"
            elif "instagram" in provider_str or "ig" in provider_str:
                provider_name = "instagram"
            elif "facebook" in provider_str or "fb" in provider_str:
                provider_name = "facebook"
            else:
                provider_name = "google_business"

            base_domain = base_url or "https://samrtautoposted.onrender.com"
            media_url = self._extract_media_url(post, db=db, base_url=base_domain)
            raw_caption = getattr(post, "caption", "") or getattr(post, "title", "") or ""
            
            caption_text = optimize_caption_for_platform(raw_caption, provider_name)
            logger.info(f"[PublishService] Provider: {provider_name} | Post ID: {getattr(post, 'id', 'new')} | Media: {media_url}")

            # ========================================================
            # 1. FACEBOOK PUBLISHING
            # ========================================================
            if provider_name == "facebook":
                fb_page_id = (
                    (getattr(social_account, "page_id", None) if social_account else None)
                    or os.getenv("FB_PAGE_ID")
                    or "1263098246886890"
                )
                fb_token = (
                    (getattr(social_account, "access_token", None) if social_account else None)
                    or os.getenv("FB_ACCESS_TOKEN")
                )

                if not fb_token:
                    return {"success": False, "error": "Facebook Page Access Token missing hai."}

                fb_provider = FacebookProvider(access_token=str(fb_token).strip(), page_id=str(fb_page_id).strip())
                return fb_provider.publish_post(post_caption=caption_text, media_url=media_url)

            # ========================================================
            # 2. INSTAGRAM PUBLISHING
            # ========================================================
            elif provider_name == "instagram":
                ig_token = (
                    (getattr(social_account, "access_token", None) if social_account else None)
                    or os.getenv("INSTAGRAM_ACCESS_TOKEN")
                )

                ig_user_id = (
                    (getattr(social_account, "instagram_id", None) if social_account else None)
                    or (getattr(social_account, "page_id", None) if social_account else None)
                    or os.getenv("INSTAGRAM_USER_ID")
                    or "17841479000604439"
                )

                if not ig_token:
                    return {"success": False, "error": "Instagram Access Token missing hai."}

                if not media_url:
                    return {"success": False, "error": "Media URL missing hai. Instagram par photo/video compulsory hai."}

                ig_provider = InstagramProvider(access_token=str(ig_token).strip(), ig_user_id=str(ig_user_id).strip())
                return ig_provider.publish_post(caption=caption_text, media_url=media_url)

            # ========================================================
            # 3. GOOGLE BUSINESS PROFILE (GMB) - Dynamic Per-User Handling
            # ========================================================
            elif provider_name == "google_business":
                gmb_token = (
                    getattr(social_account, "access_token", None)
                    or os.getenv("GOOGLE_ACCESS_TOKEN")
                )

                if not gmb_token:
                    return {"success": False, "error": "Google Business Access Token missing hai. Kripya apna Google account connect karein."}

                # Dynamic Resolution: DB ke page_id ya location_id se path nikalna
                stored_loc = str(
                    getattr(social_account, "page_id", "")
                    or getattr(social_account, "location_id", "")
                    or os.getenv("GOOGLE_LOCATION_ID", "")
                ).strip()

                stored_acc = str(
                    getattr(social_account, "account_id", "")
                    or os.getenv("GOOGLE_ACCOUNT_ID", "")
                ).strip()

                account_id = None
                location_id = None

                # Clean format detection: accounts/123/locations/456 ya 123/456 ya plain ID
                if "/" in stored_loc:
                    parts = [p for p in stored_loc.split("/") if p]
                    if "accounts" in parts and "locations" in parts:
                        account_id = parts[parts.index("accounts") + 1]
                        location_id = parts[parts.index("locations") + 1]
                    elif len(parts) >= 2:
                        account_id = parts[0]
                        location_id = parts[1]
                    else:
                        location_id = stored_loc
                else:
                    location_id = stored_loc
                    account_id = stored_acc or None

                refresh_token = getattr(social_account, "refresh_token", None)

                # CTA button and Action URL extraction
                raw_meta = getattr(post, "post_metadata", None) or getattr(post, "extra_data", None) or {}
                if isinstance(raw_meta, str):
                    try:
                        raw_meta = json.loads(raw_meta)
                    except Exception:
                        raw_meta = {}
                elif not isinstance(raw_meta, dict):
                    raw_meta = {}

                action_type = raw_meta.get("action_type") or getattr(post, "action_type", None)
                action_url = raw_meta.get("cta_url") or raw_meta.get("action_url") or getattr(post, "action_url", None)

                logger.info(f"[PublishService GMB Dispatch] Account: {account_id} | Location: {location_id} | Media: {media_url}")

                gmb_provider = GoogleBusinessProvider(
                    access_token=str(gmb_token).strip(),
                    location_id=str(location_id).strip() if location_id else None,
                    account_id=str(account_id).strip() if account_id else None,
                    refresh_token=str(refresh_token).strip() if refresh_token else None
                )

                result = gmb_provider.publish_post(
                    summary=caption_text,
                    media_url=media_url,
                    action_type=action_type,
                    action_url=action_url,
                    topic_type="STANDARD"
                )

                return result

            # ========================================================
            # 4. LINKEDIN PUBLISHING
            # ========================================================
            elif provider_name == "linkedin":
                li_token = getattr(social_account, "access_token", None)
                author_urn = getattr(social_account, "page_id", None)

                if not li_token:
                    return {"success": False, "error": "LinkedIn Access Token missing hai."}

                if not author_urn:
                    return {"success": False, "error": "LinkedIn Author URN / Page ID missing hai."}

                headers = {
                    "Authorization": f"Bearer {str(li_token).strip()}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Content-Type": "application/json"
                }

                share_body = {
                    "author": str(author_urn).strip(),
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": caption_text},
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
                }

                if media_url:
                    share_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                    share_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                        {
                            "status": "READY",
                            "description": {"text": caption_text[:200]},
                            "originalUrl": media_url,
                            "title": {"text": getattr(post, "title", "Post Update") or "Post Update"}
                        }
                    ]

                response = requests.post(
                    "https://api.linkedin.com/v2/ugcPosts",
                    headers=headers,
                    json=share_body,
                    timeout=15
                )

                if response.status_code in [200, 201]:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"LinkedIn API Error ({response.status_code}): {response.text}"}

            return {"success": False, "error": f"Unsupported platform: {provider_name}"}

        except Exception as e:
            logger.exception(f"Unexpected exception in PublishService.publish_to_platform: {e}")
            return {"success": False, "error": str(e)}

    def publish_post(self, db, post, base_url: str = "") -> dict:
        """
        Helper method to resolve post's social account and dispatch
        """
        social_account = getattr(post, "social_account", None)
        if not social_account and getattr(post, "social_account_id", None):
            from app.models.social_account import SocialAccount
            social_account = db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()

        return self.publish_to_platform(post=post, social_account=social_account, db=db, base_url=base_url)