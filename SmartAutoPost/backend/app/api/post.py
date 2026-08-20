from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permission import check_user_permission
from app.models.user import User
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