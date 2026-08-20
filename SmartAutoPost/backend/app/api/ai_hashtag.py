from fastapi import APIRouter

from app.schemas.ai_hashtag import (
    HashtagRequest,
    HashtagResponse,
)

from app.services.ai_hashtag_service import AIHashtagService


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

service = AIHashtagService()


@router.post(
    "/generate-hashtags",
    response_model=HashtagResponse,
)
def generate_hashtags(data: HashtagRequest):

    return service.generate_hashtags(data)