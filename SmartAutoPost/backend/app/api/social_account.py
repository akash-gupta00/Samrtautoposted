import os
import logging
import requests
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

# Database session dependency
try:
    from app.database.session import get_db
except ImportError:
    try:
        from app.database import get_db
    except ImportError:
        try:
            from app.core.database import get_db
        except ImportError:
            from app.db.session import get_db

from app.models.social_account import SocialAccount

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social-accounts", tags=["Social Accounts"])


@router.get("/")
def get_connected_accounts(
    organization_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(SocialAccount)
    if organization_id:
        query = query.filter(SocialAccount.organization_id == organization_id)
    return query.all()


@router.get("/google/callback")
def google_oauth_callback(
    code: str,
    state: Optional[str] = None,
    organization_id: Optional[int] = Query(15),
    db: Session = Depends(get_db)
):
    """
    Google OAuth Callback: Fetches business locations automatically
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "https://samrtautoposted.onrender.com/api/v1/social-accounts/google/callback"
    )

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth credentials are not configured.")

    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    try:
        token_res = requests.post(token_url, data=token_payload, timeout=15)
        token_data = token_res.json()
    except Exception as e:
        logger.error(f"[Google OAuth] Token exchange error: {e}")
        raise HTTPException(status_code=400, detail="Google token exchange failed.")

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        error_desc = token_data.get("error_description", token_data.get("error", "No access token received"))
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {error_desc}")

    headers = {"Authorization": f"Bearer {access_token}"}
    connected_locations = []

    try:
        acc_res = requests.get(
            "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
            headers=headers,
            timeout=15
        ).json()
        accounts = acc_res.get("accounts", [])
    except Exception as e:
        logger.warning(f"[Google OAuth] Account discovery warning: {e}")
        accounts = []

    for acc in accounts:
        acc_name = acc.get("name")
        account_title = acc.get("accountName", "Google Business Listing")

        if not acc_name:
            continue

        try:
            loc_res = requests.get(
                f"https://mybusinessbusinessinformation.googleapis.com/v1/{acc_name}/locations?readMask=name,title,storeCode",
                headers=headers,
                timeout=15
            ).json()
            locations = loc_res.get("locations", [])
        except Exception as e:
            logger.warning(f"[Google OAuth] Location discovery failed for {acc_name}: {e}")
            locations = []

        for loc in locations:
            loc_name = loc.get("name")
            loc_title = loc.get("title", account_title)
            full_identifier = f"{acc_name}/{loc_name.split('/')[-1]}"

            existing = db.query(SocialAccount).filter(
                SocialAccount.organization_id == organization_id,
                SocialAccount.provider == "google_business",
                SocialAccount.page_id == full_identifier
            ).first()

            if existing:
                existing.access_token = access_token
                if refresh_token:
                    existing.refresh_token = refresh_token
                existing.account_name = loc_title
                existing.is_active = True
            else:
                new_acc = SocialAccount(
                    organization_id=organization_id,
                    provider="google_business",
                    platform="google_business",
                    account_name=loc_title,
                    page_id=full_identifier,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    is_active=True
                )
                db.add(new_acc)

            connected_locations.append(loc_title)

    if not connected_locations:
        existing_generic = db.query(SocialAccount).filter(
            SocialAccount.organization_id == organization_id,
            SocialAccount.provider == "google_business"
        ).first()

        if existing_generic:
            existing_generic.access_token = access_token
            if refresh_token:
                existing_generic.refresh_token = refresh_token
            existing_generic.is_active = True
        else:
            fallback_acc = SocialAccount(
                organization_id=organization_id,
                provider="google_business",
                platform="google_business",
                account_name="Google Business Profile",
                page_id="default",
                access_token=access_token,
                refresh_token=refresh_token,
                is_active=True
            )
            db.add(fallback_acc)
        connected_locations.append("Google Business Account")

    db.commit()

    return {
        "success": True,
        "message": f"Successfully connected: {', '.join(connected_locations)}"
    }