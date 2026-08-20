import requests

from app.providers.social.base_provider import BaseProvider


GRAPH_API_VERSION = "v20.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class FacebookProvider(BaseProvider):
    """
    Facebook Page posting ka real implementation (Graph API).

    page_id + access_token dono Facebook PAGE ke hone chahiye
    (user ke personal profile ke nahi) -- Facebook sirf Pages par
    programmatic posting allow karta hai.

    - Agar image hai: POST /{page-id}/photos (caption + url)
    - Agar sirf text hai: POST /{page-id}/feed (message)
    """

    def __init__(self, access_token=None, page_id=None):
        self.access_token = access_token
        self.page_id = page_id

    def connect(self):
        if not self.access_token:
            return {"success": False, "message": "Facebook access token missing"}
        return {"success": True, "message": "Facebook connected successfully"}

    def publish_post(self, post_caption: str, media_url: str = None):
        try:
            if not self.access_token:
                return {"success": False, "platform": "facebook", "error": "Access token missing"}

            if not self.page_id:
                return {"success": False, "platform": "facebook", "error": "Facebook page id missing"}

            if media_url:
                url = f"{GRAPH_BASE_URL}/{self.page_id}/photos"
                payload = {"access_token": self.access_token, "caption": post_caption or "", "url": media_url}
            else:
                url = f"{GRAPH_BASE_URL}/{self.page_id}/feed"
                payload = {"access_token": self.access_token, "message": post_caption or ""}

            response = requests.post(url, data=payload, timeout=30)
            result = response.json()

            print("======================")
            print("FACEBOOK API RESPONSE")
            print(result)
            print("======================")

            if "id" not in result:
                return {"success": False, "platform": "facebook", "error": result.get("error", result)}

            return {
                "success": True,
                "platform": "facebook",
                "platform_post_id": result["id"],
                "message": "Facebook post published successfully",
            }

        except Exception as e:
            return {"success": False, "platform": "facebook", "error": str(e)}

    def delete_post(self, platform_post_id):
        try:
            url = f"https://graph.facebook.com/{platform_post_id}"
            response = requests.delete(url, params={"access_token": self.access_token}, timeout=30)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def refresh_token(self):
        return {"success": False, "message": "Facebook token refresh not implemented"}

    def fetch_analytics(self, platform_post_id):
        try:
            url = f"https://graph.facebook.com/{platform_post_id}/insights"
            response = requests.get(url, params={"access_token": self.access_token}, timeout=30)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disconnect(self):
        return {"success": True, "message": "Facebook disconnected"}
