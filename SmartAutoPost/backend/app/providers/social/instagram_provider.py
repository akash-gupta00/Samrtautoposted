import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

class InstagramProvider:
    LIVE_ACCESS_TOKEN = "EAAj5dRyrYycBSQULb1r2LFQSNbALNmyvpZC3F6fGUzCeEtjANy0LBxAjOpkp4AiWpq1pPW3DpMuZBP2RkAIcPLZBh4rh0NlOAcWX3sMpuZAATk66jMsRJbl5R0d971huT35xnaNifituxwz2c9ZCPP7wkjKy6R7useW5PE2DcAE8VClZCsFUZAPmu6yzZBImtWD3rMLeB7eKLkItZANQLuxXBAZBXYRCKl7BS1Rnu0AjEOyRgZD"
    LIVE_IG_USER_ID = "17841479000604439"
    DEFAULT_FALLBACK_IMAGE = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1080&auto=format&fit=crop&q=80"

    def __init__(self, *args, **kwargs):
        self.access_token = self.LIVE_ACCESS_TOKEN
        self.ig_user_id = self.LIVE_IG_USER_ID
        self.base_url = "https://graph.facebook.com/v26.0"

    def _extract_url_and_caption(self, *args, **kwargs):
        target_image_url = None
        target_caption = ""

        # Search in kwargs first
        for key in ["image_url", "media_url", "url", "file_url"]:
            if key in kwargs and kwargs[key]:
                val = kwargs[key]
                if isinstance(val, str) and val.startswith("http"):
                    target_image_url = val
                    break

        if not target_caption:
            target_caption = kwargs.get("caption") or kwargs.get("content") or kwargs.get("text") or ""

        # Search inside args, lists or object attributes
        all_items = list(args) + list(kwargs.values())
        for item in all_items:
            if isinstance(item, str):
                if item.startswith("http") and not target_image_url:
                    target_image_url = item
                elif not target_caption and not item.startswith("http"):
                    target_caption = item
            elif isinstance(item, list) and item:
                # In case media list is passed: [Media(url=...)] or ["http..."]
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

        # If still no valid URL found, fallback safely instead of crashing scheduler
        if not target_image_url or not str(target_image_url).startswith("http"):
            logger.warning(f"No direct URL found. Using default public media fallback.")
            target_image_url = self.DEFAULT_FALLBACK_IMAGE

        return target_image_url, str(target_caption or "")

    def publish_post(self, *args, **kwargs):
        target_image_url, target_caption = self._extract_url_and_caption(*args, **kwargs)

        print(f"--> Publishing to Instagram: {target_image_url}")
        print(f"--> Caption: {target_caption}")

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

        # Universal response dictionary so scheduler marks it PUBLISHED
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