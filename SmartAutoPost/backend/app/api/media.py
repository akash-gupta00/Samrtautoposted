import os
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.media import Media
from app.models.user import User

router = APIRouter(prefix="/media", tags=["Media"])

UPLOAD_DIR = "uploads/media"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    # Images
    "jpg", "jpeg", "png", "webp", "gif",
    # Videos / Reels
    "mp4", "mov", "avi", "m4v", "webm"
}


@router.post("/upload")
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    organization_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format .{ext}. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Unique file name generate karein
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Public Accessible Base URL
    base_url = str(request.base_url).rstrip("/")
    if "onrender.com" in base_url and base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://")

    public_url = f"{base_url}/uploads/media/{unique_filename}"
    media_type = "video" if ext in ["mp4", "mov", "avi", "m4v", "webm"] else "image"
    org_id = organization_id or getattr(current_user, "organization_id", 1) or 1

    # Safe model instantiation (Dynamic column check to prevent TypeError)
    media_kwargs = {}
    if hasattr(Media, "organization_id"):
        media_kwargs["organization_id"] = org_id
    if hasattr(Media, "url"):
        media_kwargs["url"] = public_url
    if hasattr(Media, "file_url"):
        media_kwargs["file_url"] = public_url
    if hasattr(Media, "file_path"):
        media_kwargs["file_path"] = file_path
    if hasattr(Media, "filename"):
        media_kwargs["filename"] = file.filename
    elif hasattr(Media, "file_name"):
        media_kwargs["file_name"] = file.filename
    if hasattr(Media, "media_type"):
        media_kwargs["media_type"] = media_type

    media_obj = Media(**media_kwargs)
    db.add(media_obj)
    db.commit()
    db.refresh(media_obj)

    return {
        "id": media_obj.id,
        "url": public_url,
        "file_url": public_url,
        "media_type": media_type,
        "filename": unique_filename,
    }


@router.get("/list")
@router.get("/")
def get_all_media(
    organization_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Media)
    if organization_id and hasattr(Media, "organization_id"):
        query = query.filter(Media.organization_id == organization_id)
    return query.order_by(Media.id.desc()).all()