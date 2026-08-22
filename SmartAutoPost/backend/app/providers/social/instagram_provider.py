import logging
import time
import requests

logger = logging.getLogger(__name__)


class InstagramProvider:
    def __init__(self, access_token: str, ig_user_id: str):
        self.access_token = str(access_token).strip()
        self.ig_user_id = str(ig_user_id).strip()
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def _extract_container_id(self, response_data: dict) -> str | None:
        """
        Instagram Graph API response se kisi bhi possible key se Container ID nikalta hai.
        """
        if not isinstance(response_data, dict):
            return None

        for key in ["id", "creation_id", "media_id", "container_id", "ig_id"]:
            val = response_data.get(key)
            if val is not None and str(val).strip():
                return str(val).strip()

        return None

    def _wait_for_container_ready(self, container_id: str, max_attempts: int = 20, delay: int = 5) -> tuple[bool, str]:
        """
        Video/Reel processing complete hone tak poll karta hai taaki publish kabhi fail na ho.
        """
        status_url = f"{self.base_url}/{container_id}"
        params = {
            "fields": "status_code,status",
            "access_token": self.access_token
        }

        for attempt in range(max_attempts):
            try:
                res = requests.get(status_url, params=params, timeout=15)
                data = res.json()

                status_code = data.get("status_code", "").upper()
                logger.info(f"Container {container_id} status check ({attempt + 1}/{max_attempts}): {status_code or data}")

                if status_code == "FINISHED":
                    return True, "Ready"
                elif status_code in ["ERROR", "EXPIRED"]:
                    return False, data.get("status", f"Container failed with status: {status_code}")

                # Agar IN_PROGRESS ya kuch aur hai to wait karein
                time.sleep(delay)

            except Exception as e:
                logger.warning(f"Error checking container status: {e}")
                time.sleep(delay)

        # Timeout hone par bhi ek baar publish try karne ke liye True return karein
        return True, "Timeout reached, attempting publish"

    def publish_post(self, caption: str, media_url: str) -> dict:
        """
        Instagram Feed Photo ya Reel publish karta hai fail-safe logic ke sath.
        """
        try:
            if not self.access_token or not self.ig_user_id:
                return {
                    "success": False,
                    "error": "Access token or Instagram User ID is missing."
                }

            if not media_url:
                return {
                    "success": False,
                    "error": "Media URL is required."
                }

            # 1. Detect Media Type (Video / Reel vs Image)
            video_extensions = ('.mp4', '.mov', '.avi', '.m4v', '.webm')
            clean_url = media_url.split('?')[0].lower()
            is_video = clean_url.endswith(video_extensions) or '/video/' in clean_url or 'video' in media_url.lower()

            # 2. Step 1: Create Media Container
            container_endpoint = f"{self.base_url}/{self.ig_user_id}/media"
            
            payload = {
                "access_token": self.access_token,
                "caption": caption or ""
            }

            if is_video:
                payload["media_type"] = "REELS"
                payload["video_url"] = media_url
                payload["share_to_feed"] = True
            else:
                payload["image_url"] = media_url

            logger.info(f"Creating Instagram container at {container_endpoint} (is_video={is_video})")
            
            response = requests.post(container_endpoint, data=payload, timeout=30)
            res_data = response.json()

            container_id = self._extract_container_id(res_data)

            if not container_id:
                error_info = res_data.get("error", {})
                error_message = error_info.get("message") or str(res_data)
                logger.error(f"Failed to create container: {error_message}")
                return {
                    "success": False,
                    "error": f"Instagram Container Error: {error_message}"
                }

            logger.info(f"Container created successfully. ID: {container_id}")

            # 3. Step 2: If Video, Wait for processing to complete
            if is_video:
                is_ready, msg = self._wait_for_container_ready(container_id)
                if not is_ready:
                    return {
                        "success": False,
                        "error": f"Instagram media processing failed: {msg}"
                    }
            else:
                time.sleep(2)  # Images ke liye light 2 second buffer

            # 4. Step 3: Publish Container
            publish_endpoint = f"{self.base_url}/{self.ig_user_id}/media_publish"
            publish_payload = {
                "creation_id": container_id,
                "access_token": self.access_token
            }

            logger.info(f"Publishing container {container_id} to Instagram...")
            pub_response = requests.post(publish_endpoint, data=publish_payload, timeout=30)
            pub_data = pub_response.json()

            final_post_id = self._extract_container_id(pub_data)

            if final_post_id:
                logger.info(f"Successfully published to Instagram! Post ID: {final_post_id}")
                return {
                    "success": True,
                    "platform_post_id": final_post_id,
                    "instagram_post_id": final_post_id,
                    "id": final_post_id
                }
            else:
                error_info = pub_data.get("error", {})
                error_message = error_info.get("message") or str(pub_data)
                logger.error(f"Failed to publish container: {error_message}")
                return {
                    "success": False,
                    "error": f"Instagram Publish Error: {error_message}"
                }

        except Exception as e:
            logger.exception("Unexpected exception in InstagramProvider.publish_post")
            return {
                "success": False,
                "error": str(e)
            }