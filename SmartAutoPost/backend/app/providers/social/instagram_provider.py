import time
import requests
import logging

logger = logging.getLogger(__name__)

class InstagramProvider:
    def __init__(self, access_token: str, ig_user_id: str):
        # Token aur ID ko clean sanitize karein
        self.access_token = str(access_token).strip().strip("'\"")
        self.ig_user_id = str(ig_user_id).strip().strip("'\"")
        self.graph_url = "https://graph.facebook.com/v20.0"

    def _is_video(self, url: str) -> bool:
        if not url:
            return False
        video_extensions = ('.mp4', '.mov', '.avi', '.wmv', '.m4v', '.webm')
        clean_url = url.split('?')[0].lower()
        return clean_url.endswith(video_extensions)

    def publish_post(self, caption: str, media_url: str = None):
        try:
            if not media_url:
                return {"success": False, "error": "Media URL is required for Instagram posts/reels."}

            is_reel = self._is_video(media_url)
            container_url = f"{self.graph_url}/{self.ig_user_id}/media"

            # Step 1: Create Media Container
            if is_reel:
                payload = {
                    "media_type": "REELS",
                    "video_url": media_url,
                    "caption": caption,
                    "access_token": self.access_token,
                }
            else:
                payload = {
                    "image_url": media_url,
                    "caption": caption,
                    "access_token": self.access_token,
                }

            logger.info(f"Creating Instagram container on target ID: {self.ig_user_id}")
            res = requests.post(container_url, data=payload, timeout=30).json()

            if "error" in res:
                err_msg = res["error"].get("message", "Container creation failed")
                logger.error(f"Instagram container creation error: {err_msg}")
                return {"success": False, "error": err_msg}

            creation_id = res.get("id")
            if not creation_id:
                return {"success": False, "error": "Failed to get creation_id from Instagram."}

            # Step 2: Reel/Video Processing Check Loop
            if is_reel:
                status_url = f"{self.graph_url}/{creation_id}"
                retries = 25
                while retries > 0:
                    time.sleep(3)
                    s_res = requests.get(
                        status_url,
                        params={"fields": "status_code", "access_token": self.access_token},
                        timeout=15
                    ).json()

                    status_code = s_res.get("status_code")
                    if status_code == "FINISHED":
                        break
                    elif status_code == "ERROR":
                        return {"success": False, "error": "Meta Reel processing encountered an error."}
                    elif status_code == "EXPIRED":
                        return {"success": False, "error": "Meta Reel processing container expired."}
                    
                    retries -= 1

                if retries <= 0:
                    return {"success": False, "error": "Reel processing timed out on Meta servers."}

            # Step 3: Publish Media Container
            publish_url = f"{self.graph_url}/{self.ig_user_id}/media_publish"
            pub_res = requests.post(
                publish_url,
                data={"creation_id": creation_id, "access_token": self.access_token},
                timeout=30
            ).json()

            if "error" in pub_res:
                err_msg = pub_res["error"].get("message", "Publish failed")
                logger.error(f"Instagram publish error: {err_msg}")
                return {"success": False, "error": err_msg}

            return {
                "success": True,
                "id": pub_res.get("id"),
                "platform_post_id": str(pub_res.get("id")),
                "media_type": "REELS" if is_reel else "IMAGE"
            }

        except Exception as e:
            logger.exception("Unexpected error in InstagramProvider")
            return {"success": False, "error": str(e)}