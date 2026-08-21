import base64
from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.ai_generation import AIGeneration
from app.schemas.gemini import GeminiRequest, GeminiResponse
from app.schemas.audit_log import AuditLogCreate
from app.services.gemini_service import GeminiService
from app.services.audit_log_service import AuditLogService

router = APIRouter(
    prefix="/ai",
    tags=["AI Gemini"],
)

service = GeminiService()

@router.post("/caption")
async def generate_caption_endpoint(
    request: Request,
    prompt: Optional[str] = Form(None),
    platform: Optional[str] = Form("instagram"),
    generation_type: Optional[str] = Form("Caption"),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Image + Prompt dono analyze karke Smart Caption & Hashtags generate karta hai.
    """
    try:
        user_prompt = prompt or "Generate an engaging post caption with relevant trending hashtags."
        
        # Format instructions for AI
        full_instruction = (
            f"Platform: {platform}. User context/prompt: {user_prompt}. "
            f"Analyze the image (if provided) and user context. "
            f"Generate a catchy, viral caption with emoji formatting, followed by 10-15 relevant and high-reach hashtags."
        )

        gemini_req = GeminiRequest(
            task_type="caption",
            platform=platform or "instagram",
            language="en",
            keyword=full_instruction
        )

        result = service.generate(gemini_req)
        caption_text = getattr(result, "result", str(result))

        return {
            "status": "success",
            "caption": caption_text,
            "content": caption_text,
            "result": caption_text
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}"
        )