import requests

from app.providers.social.base_provider import BaseProvider


# Instagram Graph API version. Meta har kuch mahine me version
# badalta rehta hai -- zaroorat pade to yahan update kar dena.
GRAPH_API_VERSION = "v21.0"
GRAPH_BASE_URL = f"https://graph.instagram.com/{GRAPH_API_VERSION}"


class InstagramProvider(BaseProvider):
    """
    Instagram API with Instagram Login (2024+) ka real implementation.

    Content publish karne ke liye Instagram ka process do steps me hota hai:
      1. Media container banao  -> POST /{ig-user-id}/media
      2. Container publish karo -> POST /{ig-user-id}/media_publish

    ig_user_id = SocialAccount.page_id (Instagram Business Account ID,
    jo login ke waqt graph.instagram.com/me se milta hai).

    IMPORTANT: Instagram par sirf image/video wala post ja sakta hai --
    plain text-only post Instagram feed par publish nahi ho sakta
    (ye Instagram ki khud ki limitation hai, humare code ki nahi).
    """

    def __init__(self, access_token=None, ig_user_id=None):
        self.access_token = access_token
        self.ig_user_id = ig_user_id

    def connect(self):
        if not self.access_token:
            return {"success": False, "message": "Instagram access token missing"}
        return {"success": True, "message": "Instagram connected successfully"}

    def publish_post(self, post_caption: str, media_url: str = None):
        try:
            if not self.access_token:
                return {"success": False, "platform": "instagram", "error": "Access token missing"}

            if not self.ig_user_id:
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "Instagram Business Account ID missing (social account ka page_id set nahi hai)",
                }

            if not media_url:
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "Instagram par photo/video ke bina post nahi ja sakta. Post me kam se kam ek image/video attach karein.",
                }

            container_url = f"{GRAPH_BASE_URL}/{self.ig_user_id}/media"
            container_payload = {
                "image_url": media_url,
                "caption": post_caption or "",
                "access_token": self.access_token,
            }

            container_response = requests.post(container_url, data=container_payload, timeout=30)
            container_result = container_response.json()

            print("======================")
            print("INSTAGRAM CONTAINER RESPONSE")
            print(container_result)
            print("======================")

            creation_id = container_result.get("id")

            if not creation_id:
                return {"success": False, "platform": "instagram", "error": container_result.get("error", container_result)}

            publish_url = f"{GRAPH_BASE_URL}/{self.ig_user_id}/media_publish"
            publish_payload = {"creation_id": creation_id, "access_token": self.access_token}

            publish_response = requests.post(publish_url, data=publish_payload, timeout=30)
            publish_result = publish_response.json()

            print("======================")
            print("INSTAGRAM PUBLISH RESPONSE")
            print(publish_result)
            print("======================")

            if "id" not in publish_result:
                return {"success": False, "platform": "instagram", "error": publish_result.get("error", publish_result)}

            return {
                "success": True,
                "platform": "instagram",
                "platform_post_id": publish_result["id"],
                "message": "Instagram post published successfully",
            }

        except Exception as e:
            return {"success": False, "platform": "instagram", "error": str(e)}

    def delete_post(self, platform_post_id):
        try:
            url = f"https://graph.instagram.com/{platform_post_id}"
            response = requests.delete(url, params={"access_token": self.access_token}, timeout=30)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def refresh_token(self):
        try:
            url = "https://graph.instagram.com/refresh_access_token"
            response = requests.get(
                url,
                params={"grant_type": "ig_refresh_token", "access_token": self.access_token},
                timeout=30,
            )
            result = response.json()
            if "access_token" in result:
                return {"success": True, "access_token": result["access_token"], "expires_in": result.get("expires_in")}
            return {"success": False, "error": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fetch_analytics(self, platform_post_id):
        try:
            url = f"{GRAPH_BASE_URL}/{platform_post_id}/insights"
            response = requests.get(
                url,
                params={"metric": "reach,impressions,likes,comments,shares,saved", "access_token": self.access_token},
                timeout=30,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disconnect(self):
        return {"success": True, "message": "Instagram disconnected"}
