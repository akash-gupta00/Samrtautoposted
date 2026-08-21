import time
import requests


class InstagramProvider:
    def __init__(self, access_token: str, ig_user_id: str):
        self.access_token = str(access_token).strip()
        self.ig_user_id = str(ig_user_id).strip()
        self.graph_url = "https://graph.facebook.com/v20.0"

    def _is_video(self, url: str) -> bool:
        """Extension check to detect Video/Reel"""
        video_extensions = ('.mp4', '.mov', '.avi', '.wmv', '.m4v', '.webm')
        clean_url = url.split('?')[0].lower()
        return clean_url.endswith(video_extensions)

    def publish_post(self, caption: str, media_url: str = None):
        """
        Photo aur Video/Reel dono ko auto-detect karke Instagram par publish karega.
        """
        try:
            if not media_url:
                return {"success": False, "error": "Instagram requires media (Photo or Video URL)."}

            is_reel = self._is_video(media_url)

            # =========================================================
            # CASE 1: INSTAGRAM REELS (Video Upload)
            # =========================================================
            if is_reel:
                # 1. Reels Container Create karein
                container_url = f"{self.graph_url}/{self.ig_user_id}/media"
                payload = {
                    "media_type": "REELS",
                    "video_url": media_url,
                    "caption": caption,
                    "access_token": self.access_token,
                }
                res = requests.post(container_url, data=payload, timeout=30)
                data = res.json()

                if "error" in data:
                    return {"success": False, "error": data["error"].get("message", "Reel container creation error")}

                creation_id = data.get("id")

                # 2. Meta Video Processing status poll karein (Reels process hone me time leti hai)
                status_url = f"{self.graph_url}/{creation_id}"
                max_retries = 20  # Max 60 seconds wait
                while max_retries > 0:
                    time.sleep(3)
                    status_res = requests.get(
                        status_url,
                        params={"fields": "status_code", "access_token": self.access_token},
                        timeout=10
                    ).json()
                    
                    status_code = status_res.get("status_code")

                    if status_code == "FINISHED":
                        break
                    elif status_code == "ERROR":
                        return {"success": False, "error": "Meta failed to process Reel video."}
                    
                    max_retries -= 1

                # 3. Reel Publish karein
                publish_url = f"{self.graph_url}/{self.ig_user_id}/media_publish"
                pub_res = requests.post(
                    publish_url,
                    data={"creation_id": creation_id, "access_token": self.access_token},
                    timeout=30,
                )
                pub_data = pub_res.json()

                if "error" in pub_data:
                    return {"success": False, "error": pub_data["error"].get("message", "Reel publish failed")}

                return {
                    "success": True,
                    "id": pub_data.get("id"),
                    "platform_post_id": str(pub_data.get("id")),
                    "media_type": "REELS",
                }

            # =========================================================
            # CASE 2: SINGLE PHOTO POST
            # =========================================================
            else:
                container_url = f"{self.graph_url}/{self.ig_user_id}/media"
                payload = {
                    "image_url": media_url,
                    "caption": caption,
                    "access_token": self.access_token,
                }
                res = requests.post(container_url, data=payload, timeout=20)
                data = res.json()

                if "error" in data:
                    return {"success": False, "error": data["error"].get("message", "Image container creation error")}

                creation_id = data.get("id")

                publish_url = f"{self.graph_url}/{self.ig_user_id}/media_publish"
                pub_res = requests.post(
                    publish_url,
                    data={"creation_id": creation_id, "access_token": self.access_token},
                    timeout=20,
                )
                pub_data = pub_res.json()

                if "error" in pub_data:
                    return {"success": False, "error": pub_data["error"].get("message", "Photo publish failed")}

                return {
                    "success": True,
                    "id": pub_data.get("id"),
                    "platform_post_id": str(pub_data.get("id")),
                    "media_type": "IMAGE",
                }

        except Exception as e:
            return {"success": False, "error": str(e)}