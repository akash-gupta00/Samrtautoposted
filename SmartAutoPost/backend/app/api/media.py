# FastAPI se APIRouter, Depends, UploadFile aur File import kar rahe hain.
# APIRouter routes group karne ke liye.
# Depends dependency injection ke liye.
# UploadFile uploaded file handle karne ke liye.
# File Swagger me file input create karne ke liye.
from fastapi import APIRouter, Depends, UploadFile, File


# SQLAlchemy Session import kar rahe hain.
# Database session type ke liye.
from sqlalchemy.orm import Session


# Database session dependency import kar rahe hain.
# Isse API ko database connection milega.
from app.database.session import get_db


# Current logged-in user dependency import kar rahe hain.
# Isse JWT token verify hoga.
from app.dependencies.auth import get_current_user


# User model import kar rahe hain.
# current_user ka type define karne ke liye.
from app.models.user import User


# Media response schema import kar rahe hain.
# Isse API ka response proper format me milega.
from app.schemas.media import MediaResponse


# Media service import kar rahe hain.
# Upload logic service layer me handle hoga.
from app.services.media_service import MediaService


# Media router create kar rahe hain.
router = APIRouter(
    prefix="/media",
    tags=["Media"]
)


# Test API.
@router.get("/")
def media_home():

    # Simple test response.
    return {
        "message": "Media API Working"
    }


# Media upload API.
# Final URL: POST /api/v1/media/upload
@router.post("/upload", response_model=MediaResponse)
def upload_media(

    # Organization id query parameter se milega.
    organization_id: int,

    # File Swagger se upload hogi.
    file: UploadFile = File(...),

    # Database session dependency.
    db: Session = Depends(get_db),

    # Current logged-in user dependency.
    current_user: User = Depends(get_current_user)

):

    # MediaService ka object bana rahe hain.
    media_service = MediaService(db)

    # Service layer ko call kar rahe hain.
    return media_service.upload_media(
        file=file,
        organization_id=organization_id
    )
    
    # Media list API.
# Final URL: GET /api/v1/media/list?organization_id=1
@router.get("/list", response_model=list[MediaResponse])
def list_media(

    # Query parameter se organization id milegi.
    organization_id: int,

    # Database session dependency.
    db: Session = Depends(get_db),

    # Current logged-in user dependency.
    current_user: User = Depends(get_current_user)

):

    # MediaService ka object bana rahe hain.
    media_service = MediaService(db)

    # Service layer se media list return kar rahe hain.
    return media_service.list_media(
        organization_id
    )
    
    # Media delete API.
# Final URL: DELETE /api/v1/media/{media_id}
@router.delete("/{media_id}")
def delete_media(

    # URL se media id milegi.
    media_id: int,

    # Database session dependency.
    db: Session = Depends(get_db),

    # Current logged-in user dependency.
    current_user: User = Depends(get_current_user)

):

    # MediaService ka object bana rahe hain.
    media_service = MediaService(db)

    # Service layer se media delete kar rahe hain.
    return media_service.delete_media(
        media_id
    )