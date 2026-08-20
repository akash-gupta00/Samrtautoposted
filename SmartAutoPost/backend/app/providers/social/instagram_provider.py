import os
import time
import requests

class InstagramProvider:
    # Live verified credentials
    LIVE_ACCESS_TOKEN = "EAAj5dRyrYycBSQULb1r2LFQSNbALNmyvpZC3F6fGUzCeEtjANy0LBxAjOpkp4AiWpq1pPW3DpMuZBP2RkAIcPLZBh4rh0NlOAcWX3sMpuZAATk66jMsRJbl5R0d971huT35xnaNifituxwz2c9ZCPP7wkjKy6R7useW5PE2DcAE8VClZCsFUZAPmu6yzZBImtWD3rMLeB7eKLkItZANQLuxXBAZBXYRCKl7BS1Rnu0AjEOyRgZD"
    LIVE_IG_USER_ID = "17841479000604439"

    def __init__(self, *args, **kwargs):
        self.access_token = self.LIVE_ACCESS_TOKEN
        self.ig_user_id = self.LIVE_IG_USER_ID
        self.base_url = "https://graph.facebook.com/v26.0"

    def publish_post(self, image_url: str = None, caption: str = "", media_url: str = None, **kwargs):
        # Public direct test image URL
        target_image_url = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1080&auto=format&fit=crop&q=80"
        
        # 1. Create Media Container
        container_url = f"{self.base_url}/{self.ig_user_id}/media"
        container_payload = {
            "image_url": target_image_url,
            "caption": caption or "SmartAutoPost Live Test 🚀",
            "access_token": self.access_token
        }
        
        container_res = requests.post(container_url, data=container_payload)
        container_data = container_res.json()
        
        if "id" not in container_data:
            raise Exception(f"Failed to create media container: {container_data}")

        creation_id = container_data["id"]
        time.sleep(4)

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

    def publish(self, *args, **kwargs):
        return self.publish_post(*args, **kwargs)