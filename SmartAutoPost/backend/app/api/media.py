import os
import shutil
import uuid
import urllib.parse
import re
from typing import Optional
import requests
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
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


class GenerateImageRequest(BaseModel):
    prompt: str
    organization_id: Optional[int] = None


def sanitize_and_build_prompt(raw_text: str) -> str:
    """
    Cleans banner/offer jargon and Hinglish fillers, converting intents
    into sharp commercial visual photography prompts for image diffusion models.
    """
    cleaned = re.sub(r'[\"*\'_`~%0-9]', '', raw_text).strip()
    cleaned = re.sub(r'\bmarble\b', 'marvel', cleaned, flags=re.IGNORECASE)

    # Words that make AI generate exterior shops or blank banners instead of subjects
    remove_words = [
        "banner", "poster", "offer", "off", "discount", "sale",
        "ka image do", "ki image do", "ka photo do", "ki photo do", "ki photo", 
        "ka photo", "banao", "chahiye", "photo do", "image do", "picture of", 
        "photo of", "uska image", "ki image", "ka me jo", "hai uska", "ka hero ka", "ka hero"
    ]
    lower = cleaned.lower()
    for rw in remove_words:
        lower = lower.replace(rw, " ")

    clean_subject = " ".join(lower.split())
    if not clean_subject:
        clean_subject = "gourmet food"

    # Direct high-impact visual overrides
    if "burger" in clean_subject:
        return "Gourmet double cheeseburger with melted cheddar and crispy golden fries on wooden tray, appetizing commercial food photography, studio lighting, 8k"
    if "pizza" in clean_subject:
        return "Freshly baked artisan pizza with melting mozzarella cheese and basil toppings, dark rustic table, commercial food photography, 8k"
    if "coffee" in clean_subject or "cafe" in clean_subject:
        return "Hot cup of cappuccino with elegant latte art on rustic wooden table with roasted coffee beans, cozy cafe lighting, high resolution"
    if any(k in clean_subject for k in ["spiderman", "spider-man", "peter parker"]):
        return "Spider-Man in iconic red and blue Marvel superhero suit on city rooftop at sunset, cinematic lighting, photorealistic movie still, 8k"
    if any(k in clean_subject for k in ["ganesh", "ganpati"]):
        return "Magnificent Lord Ganesha idol with intricate golden jewelry and traditional floral decorations, radiant warm divine light, 8k"
    if "gym" in clean_subject or "fitness" in clean_subject:
        return "Modern luxury gym equipment with cinematic moody lighting, professional fitness photography"

    return f"Professional commercial photography of {clean_subject}, high resolution, studio lighting, sharp focus, 8k"


@router.post("/generate-image")
async def generate_ai_image(
    payload: GenerateImageRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Please enter an image description.")

    # 1. Sanitize & build photographic prompt
    visual_prompt = sanitize_and_build_prompt(payload.prompt)
    encoded_prompt = urllib.parse.quote(visual_prompt)
    seed = uuid.uuid4().int % 1000000

    # 2. Fast Diffusion URL
    ai_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&model=turbo&nologo=true&seed={seed}"
    fallback_ai_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&nologo=true&seed={seed}"

    unique_filename = f"media_{uuid.uuid4().hex}.jpg"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    image_bytes = None

    # Primary attempt
    try:
        res = requests.get(ai_url, timeout=12)
        if res.status_code == 200 and len(res.content) > 2000:
            image_bytes = res.content
    except Exception:
        pass

    # Fallback attempt
    if not image_bytes:
        try:
            res = requests.get(fallback_ai_url, timeout=15)
            if res.status_code == 200 and len(res.content) > 2000:
                image_bytes = res.content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Image generation timed out: {str(e)}. Please retry."
            )

    if not image_bytes:
        raise HTTPException(status_code=500, detail="Could not retrieve image data. Please try again.")

    # 3. Save locally
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    # 4. Construct Public URL
    base_url = str(request.base_url).rstrip("/")
    if "onrender.com" in base_url and base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://")

    public_url = f"{base_url}/uploads/media/{unique_filename}"
    org_id = payload.organization_id or getattr(current_user, "organization_id", 10) or 10

    # 5. Insert into Media Library Database
    media_kwargs = {}
    if hasattr(Media, "organization_id"):
        media_kwargs["organization_id"] = org_id
    if hasattr(Media, "file_url"):
        media_kwargs["file_url"] = public_url
    if hasattr(Media, "url"):
        media_kwargs["url"] = public_url

    clean_name = f"Post_{visual_prompt[:20].replace(' ', '_')}.jpg"
    if hasattr(Media, "filename"):
        media_kwargs["filename"] = clean_name
    elif hasattr(Media, "file_name"):
        media_kwargs["file_name"] = clean_name

    if hasattr(Media, "file_type"):
        media_kwargs["file_type"] = "image"
    if hasattr(Media, "media_type"):
        media_kwargs["media_type"] = "image"

    media_obj = Media(**media_kwargs)
    db.add(media_obj)
    db.commit()
    db.refresh(media_obj)

    return {
        "success": True,
        "id": media_obj.id,
        "image_url": public_url,
        "file_url": public_url,
        "url": public_url,
        "prompt_used": visual_prompt,
        "media_type": "image",
        "file_type": "image",
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

    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    base_url = str(request.base_url).rstrip("/")
    if "onrender.com" in base_url and base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://")

    public_url = f"{base_url}/uploads/media/{unique_filename}"
    media_kind = "video" if ext in ["mp4", "mov", "avi", "m4v", "webm"] else "image"
    org_id = organization_id or getattr(current_user, "organization_id", 10) or 10

    media_kwargs = {}
    if hasattr(Media, "organization_id"):
        media_kwargs["organization_id"] = org_id
    if hasattr(Media, "file_url"):
        media_kwargs["file_url"] = public_url
    if hasattr(Media, "url"):
        media_kwargs["url"] = public_url
    if hasattr(Media, "filename"):
        media_kwargs["filename"] = file.filename
    elif hasattr(Media, "file_name"):
        media_kwargs["file_name"] = file.filename

    if hasattr(Media, "file_type"):
        media_kwargs["file_type"] = media_kind
    if hasattr(Media, "media_type"):
        media_kwargs["media_type"] = media_kind

    media_obj = Media(**media_kwargs)
    db.add(media_obj)
    db.commit()
    db.refresh(media_obj)

    return {
        "id": media_obj.id,
        "url": public_url,
        "file_url": public_url,
        "media_type": media_kind,
        "file_type": media_kind,
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