# BaseModel import kar rahe hain.
# Request aur Response schema banane ke liye.
from pydantic import BaseModel

# Datetime import kar rahe hain.
# Schedule time store karne ke liye.
from datetime import datetime

# Optional import kar rahe hain.
from typing import Optional


# ============================================
# Schedule Create Schema
# ============================================

# User schedule create karega.
class PostScheduleCreate(BaseModel):

    # Kis post ko schedule karna hai.
    post_id: int

    # Kab publish karna hai.
    schedule_time: datetime

    # Default timezone.
    timezone: str = "Asia/Kolkata"


# ============================================
# Schedule Response Schema
# ============================================

# API response ke liye.
class PostScheduleResponse(BaseModel):

    # Schedule id.
    id: int

    # Post id.
    post_id: int

    # Publish time.
    schedule_time: datetime

    # Timezone.
    timezone: str

    # Current status.
    status: str

    # Retry count.
    retry_count: int

    # Created time.
    created_at: datetime

    # SQLAlchemy object ko support karega.
    class Config:

        # ORM support enable.
        from_attributes = True