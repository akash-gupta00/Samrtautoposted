import logging
import os
import json
import re
from datetime import datetime
from typing import List, Any, Optional
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permission import check_user_permission
from app.models.user import User
from app.models.post import Post
from app.models.media import Media
from app.models.social_account import SocialAccount
from app.models.analytics import AnalyticsRecord
from app.schemas.post import (
    AttachMediaRequest,
    PostCreate,
    PostResponse,
    PostUpdate,
)
from app.services.post_service import PostService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)

post_service = PostService()


# =========================================================
# MULTI-ACCOUNT POST CREATION SCHEMA
# =========================================================
class MultiPostCreate(BaseModel):
    organization_id: int
    account_ids: List[int]
    title: str = ""
    caption: str = ""
    media_url: Optional[str] = None
    image_url: Optional[str] = None
    media_ids: Optional[List[int]] = []
    scheduled_at: Optional[str] = None


# =========================================================
# LIVE INSTAGRAM USER SEARCH / DISCOVERY WITH LIVE AVATAR
# =========================================================
@router.get("/suggest-handles")
def search_real_instagram_users(
    query: str = Query(..., description="Real Instagram username to search"),
    db: Session = Depends(get_db)
):
    clean_query = query.strip().lstrip("@").strip().lower()
    if not clean_query:
        return {"success": True, "handles": []}

    results = []
    try:
        ig_account = db.query(SocialAccount).filter(
            SocialAccount.provider.ilike("%instagram%"),
            SocialAccount.access_token.isnot(None)
        ).first()

        token = getattr(ig_account, "access_token", None) if ig_account else None
        token = token or os.getenv("INSTAGRAM_ACCESS_TOKEN")

        ig_id = None
        if ig_account:
            ig_id = (
                getattr(ig_account, "platform_account_id", None)
                or getattr(ig_account, "account_id", None)
                or getattr(ig_account, "social_id", None)
            )

        if token and not ig_id:
            try:
                me_res = requests.get(
                    f"https://graph.facebook.com/v19.0/me?fields=instagram_business_account,id&access_token={token}",
                    timeout=5
                )
                me_data = me_res.json()
                if "instagram_business_account" in me_data and "id" in me_data["instagram_business_account"]:
                    ig_id = me_data["instagram_business_account"]["id"]
                elif "id" in me_data:
                    ig_id = me_data["id"]
            except Exception as e:
                logger.warning(f"[Suggest Handles] /me IG resolution warning: {e}")

        ig_id = ig_id or os.getenv("INSTAGRAM_USER_ID", "17841479000604439")

        if token and ig_id:
            url = f"https://graph.facebook.com/v19.0/{ig_id}?fields=business_discovery.username({clean_query}){{username,name,profile_picture_url,followers_count}}&access_token={token}"
            res = requests.get(url, timeout=6)
            data = res.json()
            
            logger.info(f"[Meta Discovery Response] for {clean_query}: {data}")

            if "business_discovery" in data:
                bd = data["business_discovery"]
                results.append({
                    "handle": f"@{bd.get('username')}",
                    "name": bd.get("name") or bd.get("username"),
                    "avatar": bd.get("profile_picture_url") or "",
                    "followers": bd.get("followers_count", 0)
                })
            else:
                logger.error(f"[Meta Graph Error]: {data.get('error')}")

    except Exception as e:
        logger.error(f"[Discovery Lookup Exception]: {e}")

    if results:
        return {"success": True, "handles": results, "is_live": True}

    return {
        "success": True,
        "handles": [
            {"handle": f"@{clean_query}", "name": clean_query, "avatar": ""}
        ],
        "is_live": False
    }


# =========================================================
# MULTI-ACCOUNT DISPATCH ENDPOINT (WITH INSTANT GMB ROUTING)
# =========================================================
@router.post("/create-multi")
def create_multi_platform_posts(
    payload: MultiPostCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_account_ids = [int(x) for x in payload.account_ids if str(x).isdigit() and int(x) > 0]

    if not target_account_ids:
        raise HTTPException(status_code=400, detail="No valid target social accounts selected.")

    created_posts = []
    errors = []

    # Priority resolution for media: direct image_url (AI) > payload.media_url > media_ids DB query
    resolved_media_url = payload.image_url or payload.media_url
    if not resolved_media_url and payload.media_ids:
        first_media = db.query(Media).filter(Media.id == payload.media_ids[0]).first()
        if first_media:
            resolved_media_url = (
                getattr(first_media, "file_url", None)
                or getattr(first_media, "url", None)
                or getattr(first_media, "file_path", None)
            )

    for acc_id in target_account_ids:
        try:
            single_post_data = PostCreate(
                organization_id=payload.organization_id,
                social_account_id=acc_id,
                title=payload.title,
                caption=payload.caption,
                media_url=resolved_media_url,
                scheduled_at=datetime.fromisoformat(payload.scheduled_at.replace("Z", "+00:00")) if payload.scheduled_at else None
            )

            created_post = post_service.create_post(
                db=db,
                post_data=single_post_data,
                current_user=current_user,
                request=request,
            )

            if resolved_media_url and hasattr(created_post, "media_url"):
                created_post.media_url = resolved_media_url
                db.commit()
                db.refresh(created_post)

            # Instant Publishing to Platform (Google Business / Meta / LinkedIn)
            if not payload.scheduled_at:
                try:
                    published_post = post_service.publish_post(
                        db=db,
                        post_id=created_post.id,
                        current_user=current_user,
                        request=request,
                    )
                    created_posts.append(published_post.id)
                except Exception as pub_err:
                    err_text = str(pub_err)
                    logger.error(f"[Publish Error for Acc {acc_id}]: {err_text}")
                    
                    if "has not been used in project" in err_text or "is disabled" in err_text:
                        err_text = "Google Business API is currently pending Google review for this project."

                    errors.append({"account_id": acc_id, "error": err_text})
                    # Post is saved in DB, so record the created ID even if instant publish errors out
                    created_posts.append(created_post.id)
            else:
                created_posts.append(created_post.id)

        except Exception as e:
            logger.error(f"Post creation failure for account {acc_id}: {e}")
            errors.append({"account_id": acc_id, "error": str(e)})

    return {
        "status": "success" if created_posts else "failed",
        "total_created": len(created_posts),
        "created_post_ids": created_posts,
        "errors": errors if errors else None
    }


# =========================================================
# STANDARD SINGLE POST ENDPOINTS
# =========================================================
@router.post("/", response_model=PostResponse)
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


@router.get("/", response_model=List[PostResponse])
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


@router.post("/{post_id}/publish", response_model=PostResponse)
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


@router.get("/{post_id}/analytics")
def get_post_analytics(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = db.query(AnalyticsRecord).filter(AnalyticsRecord.post_id == post_id).order_by(AnalyticsRecord.created_at.desc()).all()
    return records


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

    platform_post_id = getattr(post, "platform_post_id", None) or getattr(post, "ig_media_id", None)
    if not platform_post_id:
        raise HTTPException(status_code=400, detail="Post has not been published to Meta yet")

    try:
        url = f"https://graph.facebook.com/v20.0/{platform_post_id}?fields=like_count,comments_count&access_token={social_account.access_token}"
        res = requests.get(url, timeout=10)
        data = res.json()

        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"].get("message", "Meta API Error"))

        likes = data.get("like_count", 0)
        comments = data.get("comments_count", 0)

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


@router.post("/{post_id}/attach-media", response_model=PostResponse)
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


@router.put("/{post_id}/schedule", response_model=PostResponse)
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


@router.get("/{post_id}", response_model=PostResponse)
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


@router.put("/{post_id}", response_model=PostResponse)
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