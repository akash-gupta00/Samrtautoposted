from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.gemini import GeminiRequest, GeminiResponse
from app.services.gemini_service import GeminiService

# Router export name strictly 'router' hona chahiye
router = APIRouter(
    prefix="/ai",
    tags=["AI Content"]
)

service = GeminiService()


@router.post("/generate", response_model=GeminiResponse)
def generate_content(
    req: GeminiRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        text = service.generate(req)
        return GeminiResponse(result=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/caption")
async def generate_caption_endpoint(
    request: Request,
    prompt: Optional[str] = Form(None),
    platform: Optional[str] = Form("Instagram"),
    generation_type: Optional[str] = Form("caption"),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        user_prompt = prompt or "Create an engaging post caption with relevant hashtags."
        gemini_req = GeminiRequest(
            task_type=generation_type or "caption",
            platform=platform or "Instagram",
            language="en",
            keyword=user_prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"
        if image:
            image_bytes = await image.read()
            mime_type = image.content_type or "image/jpeg"

        result = service.generate(gemini_req, image_bytes=image_bytes, mime_type=mime_type)
        caption_text = getattr(result, "result", str(result))

        return {
            "status": "success",
            "caption": caption_text,
            "result": caption_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))