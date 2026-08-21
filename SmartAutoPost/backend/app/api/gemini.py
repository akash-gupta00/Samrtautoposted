from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.ai_generation import AIGeneration

from app.schemas.gemini import (
    GeminiRequest,
    GeminiResponse,
)
from app.schemas.audit_log import AuditLogCreate

from app.services.gemini_service import GeminiService
from app.services.audit_log_service import AuditLogService


router = APIRouter(
    prefix="/ai",
    tags=["AI Gemini"],
)

service = GeminiService()


class CaptionPayload(BaseModel):
    prompt: Optional[str] = None
    topic: Optional[str] = None
    platform: Optional[str] = "instagram"
    tone: Optional[str] = "engaging"
    keyword: Optional[str] = None


@router.post("/caption")
def generate_caption_endpoint(
    data: CaptionPayload,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Frontend ke AI Studio (/api/v1/ai/caption) ko handle karta hai.
    """
    try:
        user_prompt = data.prompt or data.topic or data.keyword or "Great post"

        # Gemini service request create kar rahe hain
        gemini_req = GeminiRequest(
            task_type="caption",
            platform=data.platform or "instagram",
            language="en",
            keyword=user_prompt
        )

        result = service.generate(gemini_req)
        caption_text = getattr(result, "result", str(result))

        return {
            "status": "success",
            "caption": caption_text,
            "content": caption_text,
            "result": caption_text,
            "data": caption_text
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Caption generation failed: {str(e)}"
        )


@router.post(
    "/gemini-generate",
    response_model=GeminiResponse,
)
def gemini_generate(
    data: GeminiRequest,
    organization_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gemini se content generate karega aur logs save karega.
    """
    try:
        result = service.generate(data)

        generation_log = AIGeneration(
            user_id=current_user.id,
            organization_id=organization_id,
            generation_type=data.task_type,
            platform=data.platform,
            prompt=data.keyword,
            generated_content=result.result,
            status="success",
            error_message=None,
        )

        db.add(generation_log)
        db.commit()
        db.refresh(generation_log)

        AuditLogService.create_log(
            db=db,
            audit_data=AuditLogCreate(
                user_id=current_user.id,
                organization_id=organization_id,
                action="ai_generation_success",
                entity_type="ai_generation",
                entity_id=generation_log.id,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get("user-agent"),
                details={
                    "task_type": data.task_type,
                    "platform": data.platform,
                    "language": data.language,
                    "keyword": data.keyword,
                    "status": "success",
                },
            ),
        )

        return result

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Gemini generation failed: {str(e)}",
        )