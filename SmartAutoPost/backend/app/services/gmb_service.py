import os
import requests
import logging
from sqlalchemy.orm import Session
from app.models.gmb_account import GMBAccount
from app.providers.social.gmb_provider import GoogleBusinessProvider
from app.schemas.gmb_schema import GMBPostCreate

logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

class GMBService:
    @staticmethod
    def refresh_access_token(db: Session, account: GMBAccount) -> str:
        """Auto refreshes expired Google access token using refresh_token"""
        if not account.refresh_token:
            return account.access_token

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": account.refresh_token,
            "grant_type": "refresh_token"
        }

        res = requests.post(token_url, data=payload)
        res_data = res.json()

        if "access_token" in res_data:
            account.access_token = res_data["access_token"]
            db.commit()
            db.refresh(account)
            return account.access_token

        logger.error(f"Failed to refresh Google Token: {res_data}")
        return account.access_token

    @staticmethod
    def publish_post(db: Session, post_data: GMBPostCreate) -> dict:
        account = db.query(GMBAccount).filter(GMBAccount.id == post_data.account_id).first()
        if not account:
            return {"success": False, "error": "GMB Account not connected."}

        # Auto refresh token if needed
        valid_token = GMBService.refresh_access_token(db, account)

        provider = GoogleBusinessProvider(access_token=valid_token)
        
        # Strip prefixes if saved with full resource name
        acc_id = account.account_name.replace("accounts/", "") if account.account_name else ""
        loc_id = account.location_id.replace("locations/", "") if account.location_id else ""

        return provider.create_post(
            account_id=acc_id,
            location_id=loc_id,
            summary=post_data.summary,
            media_url=post_data.media_url,
            cta_url=post_data.cta_url
        )