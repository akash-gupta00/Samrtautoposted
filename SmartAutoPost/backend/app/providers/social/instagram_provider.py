import logging
import time
import requests
import json
import os

logger = logging.getLogger(__name__)


class InstagramProvider:
    def __init__(self, access_token: str = None, ig_user_id: str = None):
        self.access_token = str(access_token).strip() if access_token else os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        self.ig_user_id = str(ig_user_id).strip() if ig_user_id else os.getenv("INSTAGRAM_USER_ID", "17841479000604439").strip()
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def publish_post(self, caption: str, media_url: str, user_tags: list = None) -> dict:
        """
        Publishes photo/video to Instagram Business account.
        
        :param caption: Text caption with @mentions and #hashtags
        :param media_url: Absolute public URL of the image or video
        :param user_tags: Optional list of users to tag on the photo, format:
                          [{"username": "akash_dev", "x": 0.5, "y": 0.5}]
        """
        try:
            token = self.access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
            ig_id = self.ig_user_id or os.getenv("INSTAGRAM_USER_ID", "17841479000604439")

            if not token:
                return {"success": False, "error": "Instagram Access Token missing hai"}

            if not media_url:
                return {"success": False, "error": "Media URL missing hai. Instagram par photo/video compulsory hai."}

            clean_url = media_url.split("?")[0].lower()
            is_video = clean_url.endswith((".mp4", ".mov", ".m4v", ".webm", ".avi"))

            # Step 1: Create Media Container
            container_endpoint = f"{self.base_url}/{ig_id}/media"
            payload = {
                "access_token": token,
                "caption": caption or ""
            }

            if is_video:
                payload["media_type"] = "REELS"
                payload["video_url"] = media_url
                payload["share_to_feed"] = "true"
            else:
                payload["image_url"] = media_url

                # Photo Tagging (user_tags parameter)
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

            logger.info(f"Creating Container on Instagram ID {ig_id} with Media: {media_url}")
            res = requests.post(container_endpoint, data=payload, timeout=30)
            res_data = res.json()

            container_id = res_data.get("id") or res_data.get("creation_id")
            if not container_id:
                err_msg = res_data.get("error", {}).get("message", str(res_data))
                logger.error(f"IG Container Creation Failed: {err_msg}")
                return {"success": False, "error": f"Instagram Container Error: {err_msg}"}

            # Step 2: Buffer Wait (Processing buffer for Meta servers)
            time.sleep(4 if is_video else 2)

            # Step 3: Publish Container
            publish_endpoint = f"{self.base_url}/{ig_id}/media_publish"
            pub_payload = {
                "creation_id": container_id,
                "access_token": token
            }

            pub_res = requests.post(publish_endpoint, data=pub_payload, timeout=30)
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
                err_msg = pub_data.get("error", {}).get("message", str(pub_data))
                logger.error(f"IG Media Publish Failed: {err_msg}")
                return {"success": False, "error": f"Instagram Publish Error: {err_msg}"}

        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network error in InstagramProvider: {req_err}")
            return {"success": False, "error": f"Network Error: {str(req_err)}"}
        except Exception as e:
            logger.exception("Unexpected exception in InstagramProvider.publish_post")
            return {"success": False, "error": str(e)}