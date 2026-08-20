from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SubscriptionCreate(BaseModel):
    organization_id: int
    plan_id: int


class SubscriptionResponse(BaseModel):
    id: int
    organization_id: int
    plan_id: int
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)