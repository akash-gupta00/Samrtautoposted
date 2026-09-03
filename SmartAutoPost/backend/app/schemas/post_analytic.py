from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PostAnalyticBase(BaseModel):
    post_id: int
    platform: str
    platform_post_id: Optional[str] = None

    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    clicks: int = 0
    saves: int = 0

    engagement_rate: float = 0.0


class PostAnalyticCreate(PostAnalyticBase):
    pass


class PostAnalyticUpdate(BaseModel):
    platform: Optional[str] = None
    platform_post_id: Optional[str] = None

    impressions: Optional[int] = None
    reach: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    clicks: Optional[int] = None
    saves: Optional[int] = None

    engagement_rate: Optional[float] = None


class PostAnalyticResponse(PostAnalyticBase):
    id: int
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )