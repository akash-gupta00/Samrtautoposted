from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CalendarPostResponse(BaseModel):
    id: int
    title: str
    caption: str
    status: str
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    social_account_id: Optional[int]

    class Config:
        from_attributes = True