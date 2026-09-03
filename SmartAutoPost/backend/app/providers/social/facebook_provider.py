import logging
import requests
import json
import os

logger = logging.getLogger(__name__)


class FacebookProvider:
    def __init__(self, access_token: str = None, page_id: str = None):
        self.access_token = str(access_token).strip() if access_token else os.getenv("FB_ACCESS_TOKEN", "").strip()
        self.page_id = str(page_id).strip() if page_id else os.getenv("FB_PAGE_ID", "1263098246886890").strip()
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def publish_post(self, post_caption: str, media_url: str = None, page_tags: list = None) -> dict:
        """
        Publishes text, photo, or video to a Facebook Page.
        page_tags format: [{"tag_uid": "TARGET_PAGE_ID", "x": 50, "y": 50}]
        """
        try:
            token = self.access_token or os.getenv("FB_ACCESS_TOKEN")
            pid = self.page_id or os.getenv("FB_PAGE_ID", "1263098246886890")

            if not token:
                return {"success": False, "error": "Facebook Page Access Token missing hai"}

            # 1. Media Type Detection
            clean_url = media_url.split("?")[0].lower() if media_url else ""
            is_video = clean_url.endswith((".mp4", ".mov", ".m4v", ".webm", ".avi"))

            # Case A: Video Post
            if media_url and is_video:
                endpoint = f"{self.base_url}/{pid}/videos"
                payload = {
                    "access_token": token,
                    "description": post_caption or "",
                    "file_url": media_url
                }
                res = requests.post(endpoint, data=payload, timeout=40)

            # Case B: Photo Post (Supports Photo Tagging)
            elif media_url:
                endpoint = f"{self.base_url}/{pid}/photos"
                payload = {
                    "access_token": token,
                    "caption": post_caption or "",
                    "url": media_url
                }
                
                # Agar photo par kisi Facebook Page ko tag karna ho
                if page_tags and isinstance(page_tags, list):
                    payload["tags"] = json.dumps(page_tags)

                res = requests.post(endpoint, data=payload, timeout=30)

            # Case C: Text-Only Post
            else:
                endpoint = f"{self.base_url}/{pid}/feed"
                payload = {
                    "access_token": token,
                    "message": post_caption or ""
                }
                res = requests.post(endpoint, data=payload, timeout=20)

            res_data = res.json()

            # Facebook API Success Response Check
            post_id = res_data.get("id") or res_data.get("post_id")
            if post_id:
                logger.info(f"Successfully published to Facebook Page! ID: {post_id}")
                return {
                    "success": True,
                    "platform": "facebook",
                    "platform_post_id": str(post_id),
                    "post_id": str(post_id),
                    "id": str(post_id)
                }
            else:
                err_msg = res_data.get("error", {}).get("message", str(res_data))
                logger.error(f"Facebook Publish Error: {err_msg}")
                return {"success": False, "error": f"Facebook Publish Error: {err_msg}"}

        except Exception as e:
            logger.exception("Unexpected exception in FacebookProvider.publish_post")
            return {"success": False, "error": str(e)}