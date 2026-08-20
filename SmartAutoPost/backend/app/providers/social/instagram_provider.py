import time
import httpx


class InstagramProvider:

    def __init__(self, access_token: str, ig_user_id: str):
        # Token aur User ID ko clean aur strip karein
        self.access_token = str(access_token).strip() if access_token else ""
        self.ig_user_id = str(ig_user_id).strip() if ig_user_id else ""
        self.graph_version = "v19.0"

    def publish_post(self, caption: str, media_url: str):
        if not self.access_token:
            return {"success": False, "error": "Instagram Access Token missing hai. Account reconnect karein."}

        if not media_url:
            return {"success": False, "error": "Instagram requires a valid media_url"}

        try:
            # 1. Instagram Business ID verify karein
            try:
                check_ig = httpx.get(
                    f"https://graph.facebook.com/{self.graph_version}/{self.ig_user_id}?fields=instagram_business_account&access_token={self.access_token}",
                    timeout=15.0
                ).json()
                if "instagram_business_account" in check_ig:
                    self.ig_user_id = str(check_ig["instagram_business_account"]["id"])
            except Exception:
                pass

            # 2. Step 1: Create Container
            container_url = f"https://graph.facebook.com/{self.graph_version}/{self.ig_user_id}/media"
            container_payload = {
                "image_url": media_url,
                "caption": caption or "",
                "access_token": self.access_token,
            }

            resp = httpx.post(container_url, data=container_payload, timeout=35.0)
            data = resp.json()

            if "id" not in data:
                err_msg = data.get("error", {}).get("message", str(data))
                return {"success": False, "error": f"Container failed: {err_msg}"}

            creation_id = data["id"]

            # 3. Step 2: Wait for Meta image processing
            time.sleep(5)

            for _ in range(5):
                status_url = f"https://graph.facebook.com/{self.graph_version}/{creation_id}?fields=status_code&access_token={self.access_token}"
                status_resp = httpx.get(status_url, timeout=15.0).json()
                status = status_resp.get("status_code")
                
                if status == "FINISHED" or not status:
                    break
                elif status == "ERROR":
                    return {"success": False, "error": "Instagram media processing failed"}
                
                time.sleep(2)

            # 4. Step 3: Publish Container
            publish_url = f"https://graph.facebook.com/{self.graph_version}/{self.ig_user_id}/media_publish"
            pub_resp = httpx.post(
                publish_url,
                data={"creation_id": creation_id, "access_token": self.access_token},
                timeout=35.0
            )
            pub_data = pub_resp.json()

            if "id" not in pub_data:
                err_msg = pub_data.get("error", {}).get("message", str(pub_data))
                return {"success": False, "error": f"Publish failed: {err_msg}"}

            return {
                "success": True,
                "platform": "instagram",
                "platform_post_id": pub_data["id"]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}