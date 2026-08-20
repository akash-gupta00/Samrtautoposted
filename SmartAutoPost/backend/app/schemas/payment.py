from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    subscription_id: int
    amount: Decimal
    currency: str = "INR"
    payment_gateway: str = "manual"
    transaction_id: Optional[str] = None
    status: str = "success"


class PaymentResponse(BaseModel):
    id: int
    subscription_id: int
    amount: Decimal
    currency: str
    payment_gateway: str
    transaction_id: Optional[str]
    status: str
    paid_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)