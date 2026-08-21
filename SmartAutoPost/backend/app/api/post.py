from datetime import datetime
from typing import List, Any
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permission import check_user_permission
from app.models.user import User
from app.models.post import Post
from app.models.social_account import SocialAccount
from app.models.analytics import AnalyticsRecord
from app.schemas.post import (
    AttachMediaRequest,
    PostCreate,
    PostResponse,
    PostUpdate,
)
from app.services.post_service import PostService


router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)

post_service = PostService()


# New post create API
@router.post(
    "/",
    response_model=PostResponse,
)
def create_post(
    post_data: PostCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.create_post(
        db=db,
        post_data=post_data,
        current_user=current_user,
        request=request,
    )


# Organization ke saare posts list karega
@router.get(
    "/",
    response_model=List[PostResponse],
)
def list_posts(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.list_posts(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


# Post ko turant Instagram/Social Media par publish karne ka endpoint
@router.post(
    "/{post_id}/publish",
    response_model=PostResponse,
)
def publish_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.publish_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
        request=request,
    )


# Post analytics fetch karega
@router.get("/{post_id}/analytics")
def get_post_analytics(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = db.query(AnalyticsRecord).filter(AnalyticsRecord.post_id == post_id).order_by(AnalyticsRecord.created_at.desc()).all()
    return records


# Instagram/Meta se live metrics sync karega
@router.post("/{post_id}/sync-metrics")
def sync_post_metrics(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    social_account = db.query(SocialAccount).filter(SocialAccount.id == post.social_account_id).first()
    if not social_account or not social_account.access_token:
        raise HTTPException(status_code=400, detail="Social account or Access Token missing")

    # Meta platform post ID check
    platform_post_id = getattr(post, "platform_post_id", None) or getattr(post, "ig_media_id", None)
    if not platform_post_id:
        raise HTTPException(status_code=400, detail="Post has not been published to Meta yet")

    try:
        # Fetch Likes and Comments from Meta Graph API
        url = f"https://graph.facebook.com/v20.0/{platform_post_id}?fields=like_count,comments_count&access_token={social_account.access_token}"
        res = requests.get(url, timeout=10)
        data = res.json()

        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"].get("message", "Meta API Error"))

        likes = data.get("like_count", 0)
        comments = data.get("comments_count", 0)

        # Fetch Insights if available
        insights_url = f"https://graph.facebook.com/v20.0/{platform_post_id}/insights?metric=impressions,reach,saved&access_token={social_account.access_token}"
        ins_res = requests.get(insights_url, timeout=10)
        ins_data = ins_res.json()

        impressions = 0
        reach = 0
        if "data" in ins_data:
            for item in ins_data["data"]:
                if item.get("name") == "impressions":
                    impressions = item.get("values", [{}])[0].get("value", 0)
                elif item.get("name") == "reach":
                    reach = item.get("values", [{}])[0].get("value", 0)

        # Save record to Database
        record = AnalyticsRecord(
            post_id=post.id,
            likes=likes,
            comments=comments,
            impressions=impressions or likes,
            reach=reach or likes,
            created_at=datetime.utcnow()
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {"status": "success", "likes": likes, "comments": comments, "impressions": impressions, "reach": reach}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# Existing post me media attach karega
@router.post(
    "/{post_id}/attach-media",
    response_model=PostResponse,
)
def attach_media(
    post_id: int,
    data: AttachMediaRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.attach_media_to_post(
        db=db,
        post_id=post_id,
        data=data,
        current_user=current_user,
        request=request,
    )


# Post ko schedule karega
@router.put(
    "/{post_id}/schedule",
    response_model=PostResponse,
)
def schedule_post(
    post_id: int,
    scheduled_at: datetime,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.schedule_post(
        db=db,
        post_id=post_id,
        scheduled_at=scheduled_at,
        current_user=current_user,
        request=request,
    )


# Single post ki detail return karega
@router.get(
    "/{post_id}",
    response_model=PostResponse,
)
def get_post_detail(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.get_post_detail(
        db=db,
        post_id=post_id,
        current_user=current_user,
    )


# Post update API
@router.put(
    "/{post_id}",
    response_model=PostResponse,
)
def update_post(
    post_id: int,
    post_data: PostUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.update_post(
        db=db,
        post_id=post_id,
        post_data=post_data,
        current_user=current_user,
        request=request,
    )


# Post delete API
@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return post_service.delete_post(
        db=db,
        post_id=post_id,
        current_user=current_user,
        request=request,
    )