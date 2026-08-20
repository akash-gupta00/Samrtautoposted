import os
import time
import requests

class InstagramProvider:
    DEFAULT_ACCESS_TOKEN = "EAAj5dRyrYycBSQULb1r2LFQSNbALNmyvpZC3F6fGUzCeEtjANy0LBxAjOpkp4AiWpq1pPW3DpMuZBP2RkAIcPLZBh4rh0NlOAcWX3sMpuZAATk66jMsRJbl5R0d971huT35xnaNifituxwz2c9ZCPP7wkjKy6R7useW5PE2DcAE8VClZCsFUZAPmu6yzZBImtWD3rMLeB7eKLkItZANQLuxXBAZBXYRCKl7BS1Rnu0AjEOyRgZD"
    DEFAULT_IG_USER_ID = "17841479000604439"

    def __init__(self, access_token: str = None, ig_user_id: str = None, **kwargs):
        self.access_token = access_token or self.DEFAULT_ACCESS_TOKEN
        self.ig_user_id = ig_user_id or self.DEFAULT_IG_USER_ID
        self.base_url = "https://graph.facebook.com/v26.0"

    def publish_post(self, image_url: str = None, caption: str = "", media_url: str = None, **kwargs):
        """
        Step 1: Media Container create karna
        Step 2: Media Container ko Instagram par publish karna
        """
        target_image_url = image_url or media_url or kwargs.get("url")

        if not self.access_token or not self.ig_user_id:
            raise ValueError("Instagram credentials missing.")

        # 1. Create Media Container
        container_url = f"{self.base_url}/{self.ig_user_id}/media"
        container_payload = {
            "image_url": target_image_url,
            "caption": caption,
            "access_token": self.access_token
        }
        
        container_res = requests.post(container_url, data=container_payload)
        container_data = container_res.json()
        
        if "id" not in container_data:
            raise Exception(f"Failed to create media container: {container_data}")

        creation_id = container_data["id"]
        
        # Wait for Instagram to process the image container
        time.sleep(3)

        # 2. Publish Container
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

    # Alias if publisher calls `publish` instead of `publish_post`
    def publish(self, *args, **kwargs):
        return self.publish_post(*args, **kwargs)