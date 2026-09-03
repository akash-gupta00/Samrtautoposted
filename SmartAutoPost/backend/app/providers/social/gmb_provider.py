import logging
import os
import requests
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class GoogleBusinessProvider:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    SCOPES = [
        "https://www.googleapis.com/auth/business.manage",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]

    def __init__(
        self,
        access_token: Optional[str] = None,
        location_id: Optional[str] = None,
        account_id: Optional[str] = None,
        refresh_token: Optional[str] = None,
        **kwargs
    ):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.access_token = str(access_token or "").strip()
        self.refresh_token = str(refresh_token or "").strip() if refresh_token else None
        self.location_id = str(location_id or "").strip()
        self.account_id = str(account_id or "").strip() if account_id else None

    def refresh_user_token(self) -> Optional[str]:
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return None
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        try:
            res = requests.post(self.TOKEN_URL, data=data, timeout=15)
            res_json = res.json()
            if "access_token" in res_json:
                self.access_token = res_json["access_token"]
                return self.access_token
        except Exception as e:
            logger.error(f"[GMB] Token refresh failed: {e}")
        return None

    def _get_accounts_and_locations(self) -> List[Dict[str, str]]:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        pairs = []

        try:
            # 1. Fetch Accounts via Account Management API
            acc_res = requests.get(
                "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
                headers=headers,
                timeout=15
            )
            acc_data = acc_res.json()
            accounts = acc_data.get("accounts", [])

            for acc in accounts:
                acc_name = acc.get("name", "")  # format: 'accounts/123456'
                if not acc_name:
                    continue

                # 2. Fetch Locations via Business Information API
                loc_res = requests.get(
                    f"https://mybusinessbusinessinformation.googleapis.com/v1/{acc_name}/locations?readMask=name,title",
                    headers=headers,
                    timeout=15
                )
                loc_data = loc_res.json()
                for loc in loc_data.get("locations", []):
                    loc_name = loc.get("name", "")  # format: 'locations/789012'
                    if loc_name:
                        pairs.append({
                            "account": acc_name.replace("accounts/", "").strip("/"),
                            "location": loc_name.replace("locations/", "").strip("/")
                        })
        except Exception as e:
            logger.warning(f"[GMB] Discovery via v1 warning: {e}")

        return pairs

    def publish_post(
        self,
        summary: str,
        media_url: Optional[str] = None,
        action_type: Optional[str] = None,
        action_url: Optional[str] = None,
        topic_type: str = "STANDARD"
    ) -> Dict[str, Any]:
        try:
            if not self.access_token:
                if not self.refresh_user_token():
                    return {"success": False, "error": "Google Access Token is missing or invalid."}

            if not summary:
                return {"success": False, "error": "Summary / Caption is required."}

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            payload: Dict[str, Any] = {
                "languageCode": "en-US",
                "summary": summary,
                "topicType": topic_type or "STANDARD"
            }

            if media_url and str(media_url).strip():
                clean_media = str(media_url).strip()
                if not clean_media.startswith("http"):
                    clean_media = f"https://samrtautoposted.onrender.com/{clean_media.lstrip('/')}"
                payload["media"] = [{
                    "mediaFormat": "PHOTO",
                    "sourceUrl": clean_media
                }]

            clean_action = str(action_type or "").strip().upper()
            clean_url = str(action_url or "").strip()
            if clean_action and clean_action not in ["NONE", ""] and clean_url:
                payload["callToAction"] = {
                    "actionType": clean_action,
                    "url": clean_url
                }

            # Account aur Location resolve karna
            resolved_pairs = self._get_accounts_and_locations()

            if not resolved_pairs and self.location_id:
                raw_loc = self.location_id.replace("locations/", "").replace("accounts/", "").strip("/")
                raw_acc = self.account_id.replace("accounts/", "").strip("/") if self.account_id else raw_loc
                resolved_pairs.append({"account": raw_acc, "location": raw_loc})

            if not resolved_pairs:
                return {
                    "success": False,
                    "error": "No verified Google Business Profile location found on your Google Account."
                }

            last_error = "Unknown error"

            for pair in resolved_pairs:
                loc_id = pair["location"]

                # Enabled Business Information v1 API endpoint
                post_url = f"https://mybusinessbusinessinformation.googleapis.com/v1/locations/{loc_id}/localPosts"
                logger.info(f"[GMB Dispatching] -> URL: {post_url} | Payload: {payload}")

                res = requests.post(post_url, json=payload, headers=headers, timeout=25)

                # Token expire hone par refresh karke retry
                if res.status_code == 401 and self.refresh_user_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    res = requests.post(post_url, json=payload, headers=headers, timeout=25)

                if res.status_code in (200, 201):
                    res_data = res.json()
                    post_id = res_data.get("name") or res_data.get("searchUrl") or "published"
                    return {
                        "success": True,
                        "platform_post_id": str(post_id),
                        "google_post_id": str(post_id),
                        "search_url": res_data.get("searchUrl"),
                        "data": res_data
                    }
                else:
                    try:
                        err_json = res.json()
                        last_error = err_json.get("error", {}).get("message") or str(err_json)
                    except Exception:
                        last_error = res.text[:300]
                    logger.error(f"[GMB Error {res.status_code}] {last_error}")

            return {
                "success": False,
                "error": f"Google Business API Error: {last_error}"
            }

        except Exception as e:
            logger.exception(f"[GMB Exception] {e}")
            return {"success": False, "error": str(e)}


GMBProvider = GoogleBusinessProvider