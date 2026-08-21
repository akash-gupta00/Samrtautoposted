from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.media import MediaResponse
from app.services.media_service import MediaService

router = APIRouter(
    prefix="/media",
    tags=["Media"]
)


@router.get("/")
def media_home():
    return {"message": "Media API Working"}


# Media upload API: POST /api/v1/media/upload?organization_id=1
@router.post("/upload", response_model=MediaResponse)
def upload_media(
    organization_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    media_service = MediaService(db)
    return media_service.upload_media(
        file=file,
        organization_id=organization_id
    )


# Media list API: GET /api/v1/media/list?organization_id=1
@router.get("/list", response_model=List[MediaResponse])
def list_media(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    media_service = MediaService(db)
    return media_service.list_media(organization_id)


# Media delete API: DELETE /api/v1/media/{media_id}
@router.delete("/{media_id}")
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    media_service = MediaService(db)
    return media_service.delete_media(media_id)