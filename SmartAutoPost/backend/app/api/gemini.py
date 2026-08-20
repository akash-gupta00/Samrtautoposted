from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

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
    Gemini se content generate karega.

    Successful aur failed AI generation database me save karega.
    Saath me audit log bhi create karega.
    """

    try:
        # Gemini API se content generate kar rahe hain.
        result = service.generate(data)

        # Successful generation history save kar rahe hain.
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

        # Successful AI generation ka audit log.
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
        # Failed generation ka database record.
        failed_log = None

        try:
            db.rollback()

            failed_log = AIGeneration(
                user_id=current_user.id,
                organization_id=organization_id,
                generation_type=data.task_type,
                platform=data.platform,
                prompt=data.keyword,
                generated_content=None,
                status="failed",
                error_message=str(e),
            )

            db.add(failed_log)
            db.commit()
            db.refresh(failed_log)

            # Failed AI generation ka audit log.
            AuditLogService.create_log(
                db=db,
                audit_data=AuditLogCreate(
                    user_id=current_user.id,
                    organization_id=organization_id,
                    action="ai_generation_failed",
                    entity_type="ai_generation",
                    entity_id=failed_log.id,
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
                        "status": "failed",
                        "error_message": str(e),
                    },
                ),
            )

        except Exception:
            db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Gemini generation failed: {str(e)}",
        )