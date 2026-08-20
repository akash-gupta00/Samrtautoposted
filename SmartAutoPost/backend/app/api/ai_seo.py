from fastapi import APIRouter

from app.schemas.ai_seo import (
    SEORequest,
    SEOResponse,
)

from app.services.ai_seo_service import AISEOService


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

service = AISEOService()


@router.post(
    "/generate-seo",
    response_model=SEOResponse,
)
def generate_seo(data: SEORequest):

    return service.generate_seo(data)