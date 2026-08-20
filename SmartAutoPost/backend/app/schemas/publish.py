from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PublishResponse(BaseModel):
    success: bool
    message: str
    platform: Optional[str] = None
    platform_post_id: Optional[str] = None
    published_at: Optional[datetime] = None


class PublishLogResponse(BaseModel):

    id: int
    post_id: int
    platform: str
    status: str
    platform_post_id: Optional[str] = None
    response: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)