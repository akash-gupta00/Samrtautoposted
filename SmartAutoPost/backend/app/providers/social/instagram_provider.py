import logging
import time
import requests
import json
import os

logger = logging.getLogger(__name__)

class InstagramProvider:
    def __init__(self, access_token: str = None, ig_user_id: str = None):
        self.access_token = str(access_token).strip() if access_token else os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        self.ig_user_id = str(ig_user_id).strip() if ig_user_id else os.getenv("INSTAGRAM_USER_ID", "").strip()
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def publish_post(self, caption: str, media_url: str, user_tags: list = None) -> dict:
        try:
            token = self.access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
            ig_id = self.ig_user_id or os.getenv("INSTAGRAM_USER_ID")

            if not token:
                return {"success": False, "error": "Instagram Access Token missing hai"}

            if not ig_id:
                return {"success": False, "error": "Instagram User ID missing hai. Account re-connect karein."}

            if not media_url:
                return {"success": False, "error": "Media URL missing hai. Instagram par photo/video compulsory hai."}

            # Local path ko public HTTPS URL mein convert karein
            final_media_url = media_url.strip()
            if not final_media_url.startswith("http"):
                base_domain = os.getenv("APP_BASE_URL", "https://samrtautoposted.onrender.com").rstrip("/")
                final_media_url = f"{base_domain}/{final_media_url.lstrip('/')}"

            clean_url = final_media_url.split("?")[0].lower()
            is_video = clean_url.endswith((".mp4", ".mov", ".m4v", ".webm", ".avi"))

            # Step 1: Create Media Container
            container_endpoint = f"{self.base_url}/{ig_id}/media"
            payload = {
                "access_token": token,
                "caption": caption or ""
            }

            if is_video:
                payload["media_type"] = "REELS"
                payload["video_url"] = final_media_url
                payload["share_to_feed"] = "true"
            else:
                payload["image_url"] = final_media_url

                if user_tags and isinstance(user_tags, list):
                    clean_tags = []
                    for t in user_tags:
                        u = str(t.get("username", "")).lstrip("@").strip()
                        if u:
                            clean_tags.append({
                                "username": u,
                                "x": float(t.get("x", 0.5)),
                                "y": float(t.get("y", 0.5))
                            })
                    if clean_tags:
                        payload["user_tags"] = json.dumps(clean_tags)

            logger.info(f"Creating Container on IG ID {ig_id} with URL: {final_media_url}")
            res = requests.post(container_endpoint, data=payload, timeout=35)
            res_data = res.json()

            container_id = res_data.get("id") or res_data.get("creation_id")
            if not container_id:
                error_obj = res_data.get("error", {})
                err_msg = error_obj.get("message", str(res_data))
                err_code = error_obj.get("code")
                err_subcode = error_obj.get("error_subcode")
                logger.error(f"IG Container Error: Code {err_code}, Subcode {err_subcode} -> {err_msg}")
                return {"success": False, "error": f"Meta Error: {err_msg} (Code {err_code})"}

            # Step 2: Processing Buffer (Wait for Meta CDN to process media)
            time.sleep(5 if is_video else 2)

            # Step 3: Publish Container
            publish_endpoint = f"{self.base_url}/{ig_id}/media_publish"
            pub_payload = {
                "creation_id": container_id,
                "access_token": token
            }

            pub_res = requests.post(publish_endpoint, data=pub_payload, timeout=35)
            pub_data = pub_res.json()

            final_id = pub_data.get("id")
            if final_id:
                logger.info(f"Successfully published to Instagram! Post ID: {final_id}")
                return {
                    "success": True,
                    "platform": "instagram",
                    "platform_post_id": str(final_id),
                    "instagram_post_id": str(final_id),
                    "id": str(final_id)
                }
            else:
                error_obj = pub_data.get("error", {})
                err_msg = error_obj.get("message", str(pub_data))
                logger.error(f"IG Media Publish Failed: {err_msg}")
                return {"success": False, "error": f"Instagram Publish Error: {err_msg}"}

        except Exception as e:
            logger.exception("Unexpected exception in InstagramProvider.publish_post")
            return {"success": False, "error": str(e)}