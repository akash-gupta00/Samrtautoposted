import json
from datetime import datetime
from typing import List, Optional
import requests

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.analytics import AnalyticsRecord
from app.models.post import Post
from app.models.social_account import SocialAccount
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# =====================================================
# GET POST ANALYTICS (Table & History)
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

    # 1. Social Account dhundein
    social_account = None
    if post.social_account_id:
        social_account = db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()

    if not social_account:
        social_account = (
            db.query(SocialAccount)
            .filter(
                SocialAccount.organization_id == post.organization_id,
                SocialAccount.is_active == True,
            )
            .first()
        )

    if not social_account or not social_account.access_token:
        raise HTTPException(status_code=400, detail="Connected social account or access token missing")

    # 2. Token clean karein (newlines, quotes, whitespaces strip)
    token = str(social_account.access_token).strip().strip("'\"")

    # 3. Meta Platform ID check karein
    platform_post_id = (
        getattr(post, "platform_post_id", None)
        or getattr(post, "ig_media_id", None)
        or getattr(post, "external_id", None)
    )

    # Fallback: Agar column me na mile toh publish_logs table check karein
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
                    platform_post_id = (
                        res_json.get("id") 
                        or res_json.get("platform_post_id") 
                        or res_json.get("instagram_post_id") 
                        or res_json.get("media_id")
                    )
        except Exception:
            pass

    if not platform_post_id:
        raise HTTPException(
            status_code=400, 
            detail="Post has no Meta Media ID in database. Please ensure it is published to Instagram."
        )

    try:
        # 4. Likes aur Comments fetch karein Meta Graph API se
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

        # 5. Reach / Impressions fetch karein
        impressions = likes
        reach = likes
        try:
            ins_url = f"https://graph.facebook.com/v20.0/{platform_post_id}/insights"
            ins_params = {
                "metric": "impressions,reach",
                "access_token": token,
            }
            ins_res = requests.get(ins_url, params=ins_params, timeout=10)
            ins_data = ins_res.json()
            if "data" in ins_data:
                for item in ins_data["data"]:
                    if item.get("name") == "impressions":
                        impressions = item.get("values", [{}])[0].get("value", likes)
                    elif item.get("name") == "reach":
                        reach = item.get("values", [{}])[0].get("value", likes)
        except Exception:
            pass

        # 6. Database me Record Save karein
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