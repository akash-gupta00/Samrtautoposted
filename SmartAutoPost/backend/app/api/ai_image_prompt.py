from fastapi import APIRouter

from app.schemas.ai_image_prompt import (
    ImagePromptRequest,
    ImagePromptResponse,
)

from app.services.ai_image_prompt_service import (
    AIImagePromptService,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

service = AIImagePromptService()


@router.post(
    "/generate-image-prompt",
    response_model=ImagePromptResponse,
)
def generate_image_prompt(data: ImagePromptRequest):

    return service.generate_image_prompt(data)