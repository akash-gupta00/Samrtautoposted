from pydantic import BaseModel
from typing import Optional

class GMBPostCreate(BaseModel):
    account_id: int # GMBAccount table ki primary key ID
    summary: str
    media_url: Optional[str] = None
    cta_url: Optional[str] = None

class GMBPostResponse(BaseModel):
    success: bool
    post_id: Optional[str] = None
    error: Optional[str] = None