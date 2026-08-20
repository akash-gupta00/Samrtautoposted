from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RefundCreate(BaseModel):
    payment_id: int
    amount: Decimal = Field(gt=0)
    reason: str | None = None


class RefundResponse(BaseModel):
    id: int
    payment_id: int
    organization_id: int
    amount: Decimal
    currency: str
    reason: str | None
    status: str
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)