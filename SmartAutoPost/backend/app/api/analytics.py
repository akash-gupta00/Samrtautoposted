from datetime import datetime
from typing import List, Any
import requests

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.post import Post
from app.models.social_account import SocialAccount
from app.models.analytics import AnalyticsRecord
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)

analytics_service = AnalyticsService()


# Overall Dashboard Summary
@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_summary(
        db=db,
        current_user=current_user,
    )


# Single Post ke Analytics Records List karna
@router.get("/post/{post_id}")
def get_single_post_analytics(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(AnalyticsRecord)
        .filter(AnalyticsRecord.post_id == post_id)
        .order_by(AnalyticsRecord.created_at.desc())
        .all()
    )
    return records


# Meta / Instagram se Live Likes & Comments Sync karna
@router.post("/post/{post_id}/sync")
def sync_post_live_metrics(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    social_account = (
        db.query(SocialAccount)
        .filter(SocialAccount.id == post.social_account_id)
        .first()
    )
    if not social_account or not social_account.access_token:
        raise HTTPException(status_code=400, detail="Social Account or Token missing")

    # Check Meta platform ID
    platform_post_id = getattr(post, "platform_post_id", None) or getattr(post, "ig_media_id", None)
    if not platform_post_id:
        raise HTTPException(status_code=400, detail="Post not published to Instagram/Meta yet")

    try:
        # 1. Fetch Likes & Comments count
        url = f"https://graph.facebook.com/v20.0/{platform_post_id}?fields=like_count,comments_count&access_token={social_account.access_token}"
        res = requests.get(url, timeout=10)
        data = res.json()

        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"].get("message", "Meta Graph API Error"))

        likes = data.get("like_count", 0)
        comments = data.get("comments_count", 0)

        # 2. Fetch Insights (Impressions & Reach)
        impressions = 0
        reach = 0
        try:
            ins_url = f"https://graph.facebook.com/v20.0/{platform_post_id}/insights?metric=impressions,reach,saved&access_token={social_account.access_token}"
            ins_res = requests.get(ins_url, timeout=10)
            ins_data = ins_res.json()
            if "data" in ins_data:
                for item in ins_data["data"]:
                    if item.get("name") == "impressions":
                        impressions = item.get("values", [{}])[0].get("value", 0)
                    elif item.get("name") == "reach":
                        reach = item.get("values", [{}])[0].get("value", 0)
        except Exception:
            impressions = likes
            reach = likes

        # 3. Save to Database
        record = AnalyticsRecord(
            post_id=post.id,
            likes=likes,
            comments=comments,
            impressions=impressions or likes,
            reach=reach or likes,
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
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")