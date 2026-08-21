import json
from datetime import datetime
import requests

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.analytics import AnalyticsRecord
from app.models.post import Post
from app.models.social_account import SocialAccount
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# =====================================================
# GET POST ANALYTICS
# =====================================================
@router.get("/post/{post_id}")
def get_post_analytics(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    records = (
        db.query(AnalyticsRecord)
        .filter(AnalyticsRecord.post_id == post_id)
        .order_by(AnalyticsRecord.created_at.desc())
        .all()
    )

    return records


# =====================================================
# SYNC LIVE METRICS FROM INSTAGRAM / META
# =====================================================
@router.post("/post/{post_id}/sync")
def sync_post_live_metrics(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # 1. Access Token: Pehle .env se lo (jo publishing me successfully chal raha hai)
    token = getattr(settings, "INSTAGRAM_ACCESS_TOKEN", None) or getattr(settings, "META_ACCESS_TOKEN", None) or getattr(settings, "FACEBOOK_ACCESS_TOKEN", None)
    
    # Fallback: Agar .env me na mile tab database se lo
    if not token:
        social_account = None
        if post.social_account_id:
            social_account = db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()
        if not social_account:
            social_account = db.query(SocialAccount).filter(
                SocialAccount.organization_id == post.organization_id,
                SocialAccount.is_active == True
            ).first()
        if social_account and social_account.access_token:
            token = social_account.access_token

    if not token:
        raise HTTPException(status_code=400, detail="Valid access token not found in ENV or database")

    token = str(token).strip().strip("'\"")

    # 2. Meta Media ID find karein
    platform_post_id = getattr(post, "platform_post_id", None) or getattr(post, "ig_media_id", None) or getattr(post, "external_id", None)

    # Agar column me nahi hai toh publish_logs se uthao
    if not platform_post_id:
        try:
            from sqlalchemy import text
            log_row = db.execute(
                text("SELECT platform_post_id, response FROM publish_logs WHERE post_id = :pid ORDER BY id DESC LIMIT 1"),
                {"pid": post_id}
            ).fetchone()
            if log_row:
                platform_post_id = log_row[0]
                if not platform_post_id and log_row[1]:
                    res_json = json.loads(log_row[1]) if isinstance(log_row[1], str) else log_row[1]
                    platform_post_id = res_json.get("id") or res_json.get("platform_post_id") or res_json.get("instagram_post_id")
        except Exception:
            pass

    if not platform_post_id:
        raise HTTPException(status_code=400, detail="Post has no Meta Media ID in database.")

    try:
        # 3. Fetch Likes & Comments via Meta Graph API
        url = f"https://graph.facebook.com/v20.0/{platform_post_id}"
        params = {
            "fields": "like_count,comments_count",
            "access_token": token,
        }
        res = requests.get(url, params=params, timeout=15)
        data = res.json()

        if "error" in data:
            error_msg = data["error"].get("message", "Meta Graph API Error")
            raise HTTPException(status_code=400, detail=f"Meta Error: {error_msg}")

        likes = data.get("like_count", 0)
        comments = data.get("comments_count", 0)

        # 4. Fetch Insights (Impressions & Reach)
        impressions = likes
        reach = likes
        try:
            ins_url = f"https://graph.facebook.com/v20.0/{platform_post_id}/insights"
            ins_res = requests.get(ins_url, params={"metric": "impressions,reach", "access_token": token}, timeout=10)
            ins_data = ins_res.json()
            if "data" in ins_data:
                for item in ins_data["data"]:
                    if item.get("name") == "impressions":
                        impressions = item.get("values", [{}])[0].get("value", likes)
                    elif item.get("name") == "reach":
                        reach = item.get("values", [{}])[0].get("value", likes)
        except Exception:
            pass

        # 5. Database me Record Save karein
        record = AnalyticsRecord(
            post_id=post.id,
            likes=likes,
            comments=comments,
            impressions=impressions,
            reach=reach,
            created_at=datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "status": "success",
            "likes": likes,
            "comments": comments,
            "impressions": impressions,
            "reach": reach,
            "recorded_at": record.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")