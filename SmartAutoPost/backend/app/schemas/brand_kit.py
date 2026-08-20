from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class BrandKitBase(BaseModel):
    organization_id: int
    brand_name: str

    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    tone_of_voice: Optional[str] = None
    default_hashtags: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BrandKitCreate(BrandKitBase):
    pass


class BrandKitUpdate(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    tone_of_voice: Optional[str] = None
    default_hashtags: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class BrandKitResponse(BrandKitBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )