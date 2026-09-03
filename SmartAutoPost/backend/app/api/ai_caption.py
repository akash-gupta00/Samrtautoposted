from fastapi import APIRouter

from app.schemas.ai_caption import (
    CaptionRequest,
    CaptionResponse,
)

from app.services.ai_caption_service import (
    AICaptionService,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

service = AICaptionService()


@router.post(
    "/generate-caption",
    response_model=CaptionResponse,
)
def generate_caption(data: CaptionRequest):

    return service.generate_caption(data)