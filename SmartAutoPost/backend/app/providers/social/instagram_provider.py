import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

class InstagramProvider:
    LIVE_ACCESS_TOKEN = "EAAj5dRyrYycBSQULb1r2LFQSNbALNmyvpZC3F6fGUzCeEtjANy0LBxAjOpkp4AiWpq1pPW3DpMuZBP2RkAIcPLZBh4rh0NlOAcWX3sMpuZAATk66jMsRJbl5R0d971huT35xnaNifituxwz2c9ZCPP7wkjKy6R7useW5PE2DcAE8VClZCsFUZAPmu6yzZBImtWD3rMLeB7eKLkItZANQLuxXBAZBXYRCKl7BS1Rnu0AjEOyRgZD"
    LIVE_IG_USER_ID = "17841479000604439"

    def __init__(self, *args, **kwargs):
        self.access_token = self.LIVE_ACCESS_TOKEN
        self.ig_user_id = self.LIVE_IG_USER_ID
        self.base_url = "https://graph.facebook.com/v26.0"

    def publish_post(self, *args, **kwargs):
        """
        Extracts actual image URL and actual caption no matter how they are passed.
        """
        all_inputs = list(args) + list(kwargs.values())
        
        target_image_url = None
        target_caption = ""

        # Find which parameter is actually a URL
        for val in all_inputs:
            if isinstance(val, str) and (val.startswith("http://") or val.startswith("https://")):
                target_image_url = val
                break
        
        # Keyword arguments check if not found in args
        if not target_image_url:
            target_image_url = kwargs.get("image_url") or kwargs.get("media_url") or kwargs.get("url")

        # Extract caption (first non-URL string)
        for val in all_inputs:
            if isinstance(val, str) and val != target_image_url:
                target_caption = val
                break

        if not target_image_url:
            raise ValueError(f"No valid image URL found in inputs: args={args}, kwargs={kwargs}")

        print(f"--> Uploading image: {target_image_url}")
        print(f"--> With caption: {target_caption}")

        # 1. Create Media Container on Instagram
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
        
        # Wait 5 seconds for Instagram to download & process user image
        time.sleep(5)

        # 2. Publish Container to Feed
        publish_url = f"{self.base_url}/{self.ig_user_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        
        publish_res = requests.post(publish_url, data=publish_payload)
        publish_data = publish_res.json()

        if "id" not in publish_data:
            raise Exception(f"Failed to publish post: {publish_data}")

        return {
            "status": "success",
            "post_id": publish_data["id"],
            "id": publish_data["id"]
        }

    def publish(self, *args, **kwargs):
        return self.publish_post(*args, **kwargs)