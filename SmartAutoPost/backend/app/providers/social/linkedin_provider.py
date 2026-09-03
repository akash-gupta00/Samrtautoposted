import requests

from app.providers.social.base_provider import BaseProvider


LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInProvider(BaseProvider):
    """
    LinkedIn UGC Posts API ka real implementation.

    IMPORTANT (LinkedIn ki apni policy hai, humari nahi):
    Post karne ke liye LinkedIn App ko "Share on LinkedIn" product
    add karna padta hai aur usko LinkedIn se APPROVAL milna zaroori
    hai (w_member_social scope). Bina approval ke access_token milega
    login ke liye, lekin posting API 403 error dega.
    Approval https://www.linkedin.com/developers/apps se apni app
    kholke "Products" tab me "Share on LinkedIn" add karke milta hai.

    author_urn = "urn:li:person:{member_id}" -- ye member_id login ke
    waqt LinkedIn ke /userinfo (OpenID Connect) endpoint se milta hai
    aur SocialAccount.page_id me store hota hai.
    """

    def __init__(self, access_token=None, author_urn=None):
        self.access_token = access_token
        self.author_urn = author_urn

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    def connect(self):
        if not self.access_token:
            return {"success": False, "message": "LinkedIn access token missing"}
        return {"success": True, "message": "LinkedIn connected successfully"}

    def publish_post(self, post_caption: str, media_url: str = None):
        try:
            if not self.access_token:
                return {"success": False, "platform": "linkedin", "error": "Access token missing"}

            if not self.author_urn:
                return {
                    "success": False,
                    "platform": "linkedin",
                    "error": "LinkedIn member URN missing (social account ka page_id set nahi hai)",
                }

            media_category = "NONE"
            media_list = []

            if media_url:
                asset_urn = self._upload_image_asset(media_url)
                if asset_urn:
                    media_category = "IMAGE"
                    media_list = [
                        {
                            "status": "READY",
                            "description": {"text": post_caption or ""},
                            "media": asset_urn,
                            "title": {"text": "SmartAutoPost"},
                        }
                    ]

            body = {
                "author": self.author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_caption or ""},
                        "shareMediaCategory": media_category,
                        "media": media_list,
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }

            response = requests.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                json=body,
                headers=self._headers(),
                timeout=30,
            )

            print("======================")
            print("LINKEDIN API RESPONSE")
            print(response.status_code, response.text)
            print("======================")

            if response.status_code not in (200, 201):
                return {"success": False, "platform": "linkedin", "error": response.text}

            platform_post_id = response.headers.get("x-restli-id")

            if not platform_post_id:
                try:
                    platform_post_id = response.json().get("id")
                except Exception:
                    platform_post_id = None

            return {
                "success": True,
                "platform": "linkedin",
                "platform_post_id": platform_post_id,
                "message": "LinkedIn post published successfully",
            }

        except Exception as e:
            return {"success": False, "platform": "linkedin", "error": str(e)}

    def _upload_image_asset(self, media_url):
        try:
            register_body = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": self.author_urn,
                    "serviceRelationships": [
                        {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                    ],
                }
            }

            register_response = requests.post(
                f"{LINKEDIN_API_BASE}/assets?action=registerUpload",
                json=register_body,
                headers=self._headers(),
                timeout=30,
            )
            register_result = register_response.json()

            upload_mechanism = (
                register_result.get("value", {})
                .get("uploadMechanism", {})
                .get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {})
            )

            upload_url = upload_mechanism.get("uploadUrl")
            asset_urn = register_result.get("value", {}).get("asset")

            if not upload_url or not asset_urn:
                print("LinkedIn asset register failed:", register_result)
                return None

            image_bytes = requests.get(media_url, timeout=30).content

            requests.put(
                upload_url,
                data=image_bytes,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=60,
            )

            return asset_urn

        except Exception as e:
            print("LinkedIn image upload error:", str(e))
            return None

    def delete_post(self, platform_post_id):
        try:
            response = requests.delete(
                f"{LINKEDIN_API_BASE}/ugcPosts/{platform_post_id}",
                headers=self._headers(),
                timeout=30,
            )
            return {"success": response.status_code in (200, 204), "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def refresh_token(self):
        return {
            "success": False,
            "message": "LinkedIn refresh tokens sirf approved apps ko milte hain. Default flow me user ko dobara login karna padta hai.",
        }

    def fetch_analytics(self, platform_post_id):
        try:
            response = requests.get(
                f"{LINKEDIN_API_BASE}/socialActions/{platform_post_id}",
                headers=self._headers(),
                timeout=30,
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disconnect(self):
        return {"success": True, "message": "LinkedIn disconnected"}
