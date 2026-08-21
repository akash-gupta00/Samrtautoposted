import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

class InstagramProvider:
    DEFAULT_FALLBACK_IMAGE = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1080&auto=format&fit=crop&q=80"

    def __init__(self, *args, **kwargs):
        # Environment variables se token aur account ID read karein
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.ig_user_id = os.getenv("INSTAGRAM_USER_ID", "17841479000604439")
        self.base_url = "https://graph.facebook.com/v26.0"

        if not self.access_token:
            logger.error("INSTAGRAM_ACCESS_TOKEN environment variable not set!")

    def _extract_url_and_caption(self, *args, **kwargs):
        target_image_url = None
        target_caption = ""

        for key in ["image_url", "media_url", "url", "file_url"]:
            if key in kwargs and kwargs[key]:
                val = kwargs[key]
                if isinstance(val, str) and val.startswith("http"):
                    target_image_url = val
                    break

        if not target_caption:
            target_caption = kwargs.get("caption") or kwargs.get("content") or kwargs.get("text") or ""

        all_items = list(args) + list(kwargs.values())
        for item in all_items:
            if isinstance(item, str):
                if item.startswith("http") and not target_image_url:
                    target_image_url = item
                elif not target_caption and not item.startswith("http"):
                    target_caption = item
            elif isinstance(item, list) and item:
                first = item[0]
                if isinstance(first, str) and first.startswith("http"):
                    target_image_url = first
                elif hasattr(first, "url"):
                    target_image_url = first.url
                elif isinstance(first, dict):
                    target_image_url = first.get("url") or first.get("media_url")
            elif hasattr(item, "url"):
                target_image_url = item.url
            elif isinstance(item, dict):
                if not target_image_url:
                    target_image_url = item.get("url") or item.get("media_url") or item.get("image_url")
                if not target_caption:
                    target_caption = item.get("caption") or item.get("content") or ""

        if not target_image_url or not str(target_image_url).startswith("http"):
            target_image_url = self.DEFAULT_FALLBACK_IMAGE

        return target_image_url, str(target_caption or "")

    def publish_post(self, *args, **kwargs):
        if not self.access_token:
            raise ValueError("Instagram Access Token is missing in environment variables.")

        target_image_url, target_caption = self._extract_url_and_caption(*args, **kwargs)

        # 1. Create Media Container
        container_url = f"{self.base_url}/{self.ig_user_id}/media"
        container_payload = {
            "image_url": target_image_url,
            "caption": target_caption,
            "access_token": self.access_token
        }
        
        container_res = requests.post(container_url, data=container_payload)
        container_data = container_res.json()
        
        if "id" not in container_data:
            raise Exception(f"Failed to create media container: {container_data}")

        creation_id = container_data["id"]
        time.sleep(4)

        # 2. Publish Media Container
        publish_url = f"{self.base_url}/{self.ig_user_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        
        publish_res = requests.post(publish_url, data=publish_payload)
        publish_data = publish_res.json()

        if "id" not in publish_data:
            raise Exception(f"Failed to publish post: {publish_data}")

        post_id = publish_data["id"]

        return {
            "status": "success",
            "is_success": True,
            "success": True,
            "id": post_id,
            "post_id": post_id,
            "platform_post_id": post_id
        }

    def publish(self, *args, **kwargs):
        return self.publish_post(*args, **kwargs)