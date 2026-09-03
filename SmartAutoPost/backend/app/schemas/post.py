from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MediaResponse(BaseModel):
    id: int
    filename: str
    file_url: str
    file_type: str
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    organization_id: int
    social_account_id: Optional[int] = None
    title: str
    caption: str
    scheduled_at: Optional[datetime] = None
    media_ids: list[int] = Field(default_factory=list)


class PostUpdate(BaseModel):
    social_account_id: Optional[int] = None
    title: Optional[str] = None
    caption: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    media_ids: Optional[list[int]] = None


class AttachMediaRequest(BaseModel):
    media_ids: list[int]


class PostResponse(BaseModel):
    id: int
    organization_id: int
    social_account_id: Optional[int]
    title: str
    caption: str
    status: str
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    created_at: datetime
    media: list[MediaResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True